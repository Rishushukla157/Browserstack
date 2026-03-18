from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from utils.image_downloader import download_image
import time
import random
import logging

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

OPINION_URL = "https://elpais.com/opinion/"
MAX_RETRIES = 3

JUNK_WORDS = {
    "opinion", "opinión", "editorial", "columna", "tribuna",
    "análisis", "analisis", "carta", "archivo", "sección"
}

JUNK_PHRASES = [
    "partners", "personalised advertising",
    "cookies", "subscribe", "suscri"
]


# ── Helpers ───────────────────────────────────────────────────

def _random_sleep(min_s=1.5, max_s=3.5):
    """Random delay to mimic human behaviour."""
    time.sleep(random.uniform(min_s, max_s))


def _is_clean_paragraph(text):
    text_lower = text.lower()
    return (
        len(text) > 40
        and not any(phrase in text_lower[:80] for phrase in JUNK_PHRASES)
    )


def _get_soup(driver):
    """
    ✅ THE KEY HANDOFF
    Selenium renders the JS → Beautiful Soup parses the HTML.
    Call this after page is fully loaded.
    """
    html = driver.page_source        # grab fully rendered HTML from Selenium
    return BeautifulSoup(html, "html.parser")  # hand to Beautiful Soup


# ── Cookie Banner ─────────────────────────────────────────────
# ✅ Selenium handles this — BS4 can't click buttons

def accept_cookies(driver):
    try:
        btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button#didomi-notice-agree-button, button[aria-label='Aceptar']"
            ))
        )
        btn.click()
        log.info("[COOKIES] 🍪 Banner dismissed")
        _random_sleep(0.8, 1.5)
    except TimeoutException:
        log.debug("[COOKIES] No banner found — continuing")
    except Exception as e:
        log.warning(f"[COOKIES] Unexpected error: {e}")


# ── Article Links ─────────────────────────────────────────────

def get_opinion_article_links(driver, max_links=5):
    driver.get(OPINION_URL)
    _random_sleep()
    accept_cookies(driver)

    # ✅ Selenium waits for JS to render articles
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article h2 a"))
        )
    except TimeoutException:
        log.error("[LINKS] Timed out waiting for article list")
        return []

    # ✅ Hand off to Beautiful Soup
    soup = _get_soup(driver)

    # ✅ CSS Selectors inside Beautiful Soup
    anchors = soup.select("article h2 a")

    seen  = set()
    links = []
    for a in anchors:
        href = a.get("href")
        # Fix relative URLs
        if href and href.startswith("/"):
            href = "https://elpais.com" + href
        if href and "/opinion/" in href and href not in seen:
            seen.add(href)
            links.append(href)
        if len(links) == max_links:
            break

    log.info(f"[LINKS] Found {len(links)} article links")
    return links


# ── Title Extraction ──────────────────────────────────────────

def _extract_title(soup, index):
    """
    ✅ Pure Beautiful Soup + CSS Selectors.
    No Selenium needed here at all.
    """
    title_selectors = [
        "h1.a_t",
        "h1.a_e_t",
        "h1[class*='_t']",
        "h1[class*='title']",
        "h1[class*='articulo']",
        "article h1",
        "h1",
    ]

    for sel in title_selectors:
        try:
            elements = soup.select(sel)
            for el in elements:
                text = el.get_text(strip=True)
                if not text or text.lower() in JUNK_WORDS:
                    continue
                if len(text.split()) >= 2 or len(text) >= 4:
                    log.info(f"[TITLE] Matched '{sel}' → {text[:60]}")
                    return text
        except Exception as e:
            log.debug(f"[TITLE] Selector failed '{sel}': {e}")

    # Fallback 1: og:title
    og = soup.select_one("meta[property='og:title']")
    if og and og.get("content"):
        og_title = og["content"].strip().split(" | ")[0]
        log.info(f"[TITLE] From og:title → {og_title[:60]}")
        return og_title

    # Fallback 2: <title> tag
    title_tag = soup.select_one("title")
    if title_tag:
        page_title = title_tag.get_text().strip().split(" | ")[0]
        if len(page_title) >= 4:
            log.info(f"[TITLE] From <title> tag → {page_title[:60]}")
            return page_title

    log.warning(f"[TITLE] Not found for article {index}")
    return ""


# ── Content Extraction ────────────────────────────────────────

def _extract_content(soup, index):
    """
    ✅ Pure Beautiful Soup + CSS Selectors.
    Selenium already rendered the JS — BS4 just parses.
    """
    content_selectors = [
        "div[data-dtm-region='articulo_cuerpo']",
        "div.a_c",
        "div[class*='article-body']",
        "div[class*='article_body']",
        "div[class*='articulo-cuerpo']",
        "div[class*='cuerpo']",
        "div[class*='body']",
        "div[class*='content']",
        "div[class*='a_b']",
        "section[class*='article']",
        "article",
    ]

    for sel in content_selectors:
        try:
            container = soup.select_one(sel)
            if not container:
                continue
            paragraphs = container.find_all("p")
            clean = [
                p.get_text(strip=True)
                for p in paragraphs
                if _is_clean_paragraph(p.get_text(strip=True))
            ]
            if clean:
                log.info(f"[CONTENT] Matched '{sel}' ({len(clean)} paragraphs)")
                return " ".join(clean)
        except Exception as e:
            log.debug(f"[CONTENT] Selector failed '{sel}': {e}")

    # Global <p> fallback
    all_ps = soup.find_all("p")
    clean = [
        p.get_text(strip=True)
        for p in all_ps
        if _is_clean_paragraph(p.get_text(strip=True))
    ]
    if clean:
        log.info(f"[CONTENT] Global <p> fallback ({len(clean)} paragraphs)")
        return " ".join(clean)

    # Paywall detection
    page_text    = soup.get_text().lower()
    is_paywalled = any(k in page_text for k in ["suscri", "paywall", "regwall", "piano-id"])

    if is_paywalled:
        log.warning(f"[CONTENT] ⚠️ Article {index} PAYWALLED — trying subtitle")
        subtitle_selectors = [
            "h2.a_st", "h2[class*='sub']", "p.a_st", "div.a_st",
            "[class*='standfirst']", "[class*='subtitle']",
            "[class*='subhead']", "[class*='lead']",
            "[class*='deck']", "header p",
        ]
        for sel in subtitle_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if len(text) > 20:
                    log.info(f"[CONTENT] Subtitle matched: '{sel}'")
                    return f"[Paywalled — preview only] {text}"

        return "Content not available (paywalled)"

    return "Content not available"


# ── Image Extraction ──────────────────────────────────────────

IMAGE_SELECTORS = [
    "figure.a_e_m img",
    "figure[class*='article'] img",
    "div[class*='article'] figure img",
    "figure img[src*='imagenes']",
    "figure img",
    "article img",
]

def _extract_image(soup):
    """✅ Pure Beautiful Soup image extraction."""
    for sel in IMAGE_SELECTORS:
        try:
            img = soup.select_one(sel)
            if img:
                src = img.get("src") or img.get("data-src")
                if src and src.startswith("http"):
                    log.info(f"[IMAGE] Matched '{sel}' → {src[:60]}")
                    return src
        except Exception as e:
            log.debug(f"[IMAGE] Selector failed '{sel}': {e}")
    return None


# ── Main Scrape with Retry ────────────────────────────────────

def scrape_article(driver, url, index=0):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.set_page_load_timeout(60)
            driver.get(url)
            break
        except TimeoutException:
            log.warning(f"[SCRAPER] Timeout attempt {attempt}/{MAX_RETRIES} for article {index}")
            if attempt == MAX_RETRIES:
                log.error(f"[SCRAPER] All retries failed for {url}")
                return None
        except WebDriverException as e:
            log.error(f"[SCRAPER] WebDriver error on article {index}: {e}")
            if attempt == MAX_RETRIES:
                return None

    _random_sleep()
    accept_cookies(driver)
    _random_sleep()

    # ✅ Selenium renders JS → hand off to Beautiful Soup
    soup = _get_soup(driver)

    title     = _extract_title(soup, index)
    content   = _extract_content(soup, index)
    image_url = _extract_image(soup)

    local_path = None
    if image_url:
        local_path = download_image(image_url, index)

    article_data = {
        "title":            title,
        "content":          content,
        "image_url":        image_url or "",
        "image_local_path": local_path or "",
        "article_url":      url,
    }

    log.info(f"[SCRAPER] ✅ Article {index} done — '{title[:50]}'")
    _random_sleep()

    return article_data