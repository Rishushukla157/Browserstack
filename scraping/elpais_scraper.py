from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.database import db
from backend.storage import save_and_upload_image
from utils.image_downloader import download_image
import time

OPINION_URL = "https://elpais.com/opinion/"


def accept_cookies(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button#didomi-notice-agree-button, button[aria-label='Aceptar']")
            )
        )
        btn.click()
        print("[SCRAPER] 🍪 Cookie banner dismissed")
        time.sleep(1)
    except:
        pass  # no banner = fine


def get_opinion_article_links(driver):
    driver.get(OPINION_URL)
    time.sleep(2)
    accept_cookies(driver)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))

    articles = driver.find_elements(By.CSS_SELECTOR, "article h2 a")

    links = []
    for a in articles:
        href = a.get_attribute("href")
        if href and "/opinion/" in href and href not in links:
            links.append(href)
        if len(links) == 5:
            break

    return links


def _extract_title(driver, index):
    """
    Try title selectors in order.
    Filters junk by checking against known section label words.
    Falls back to og:title and <title> tag if all selectors fail.
    """
    JUNK_WORDS = {
        "opinion", "opinión", "editorial", "columna", "tribuna",
        "análisis", "analisis", "carta", "archivo", "sección"
    }

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
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                text = el.text.strip()
                if not text:
                    continue
                if text.lower() in JUNK_WORDS:
                    print(f"[SCRAPER] Skipping junk label: '{text}'")
                    continue
                if len(text.split()) >= 2 or len(text) >= 4:
                    print(f"[SCRAPER] Title matched: '{sel}' → {text[:60]}")
                    return text
        except:
            continue

    # ── Fallback 1: og:title meta tag ─────────────────────────
    try:
        og       = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
        og_title = og.get_attribute("content").strip().split(" | ")[0].strip()
        if og_title:
            print(f"[SCRAPER] Title from og:title → {og_title[:60]}")
            return og_title
    except:
        pass

    # ── Fallback 2: <title> tag ───────────────────────────────
    try:
        page_title = driver.title.strip().split(" | ")[0].strip()
        if page_title and len(page_title) >= 4:
            print(f"[SCRAPER] Title from <title> tag → {page_title[:60]}")
            return page_title
    except:
        pass

    print(f"[SCRAPER] Title not found for article {index}")
    return ""


def _extract_content(driver, index):
    """
    Try content selectors in order.
    If paywalled, still tries to get visible subtitle/standfirst.
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

    for selector in content_selectors:
        try:
            container  = driver.find_element(By.CSS_SELECTOR, selector)
            paragraphs = container.find_elements(By.TAG_NAME, "p")
            # ✅ Skip paragraphs that look like cookie consent text
            clean_paragraphs = [
                p.text.strip() for p in paragraphs
                if p.text.strip()
                and "partners" not in p.text.lower()
                and "personalised advertising" not in p.text.lower()
                and "cookies" not in p.text.lower()[:50]
            ]
            text = " ".join(clean_paragraphs)
            if text:
                print(f"[SCRAPER] Content matched: '{selector}' ({len(clean_paragraphs)} paragraphs)")
                return text
        except:
            continue

    # ── Global <p> fallback ───────────────────────────────────
    all_ps = driver.find_elements(By.TAG_NAME, "p")
    clean  = [
        p.text.strip() for p in all_ps
        if len(p.text.strip()) > 40
        and "partners" not in p.text.lower()
        and "personalised advertising" not in p.text.lower()
        and "cookies" not in p.text.lower()[:50]
    ]
    if clean:
        print(f"[SCRAPER] Content from global <p> fallback ({len(clean)} clean tags)")
        return " ".join(clean)

    # ── Paywall detection ─────────────────────────────────────
    page_src     = driver.page_source.lower()
    is_paywalled = any(k in page_src for k in ["suscri", "paywall", "regwall", "piano-id"])

    if is_paywalled:
        print(f"[SCRAPER] ⚠️  Article {index} is PAYWALLED — trying subtitle")

        subtitle_selectors = [
            "h2.a_st",
            "h2[class*='sub']",
            "p.a_st",
            "div.a_st",
            "[class*='standfirst']",
            "[class*='subtitle']",
            "[class*='subhead']",
            "[class*='lead']",
            "[class*='deck']",
            "header p",
        ]
        for sel in subtitle_selectors:
            try:
                el   = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if len(text) > 20:
                    print(f"[SCRAPER] Subtitle matched: '{sel}'")
                    return f"[Paywalled — preview only] {text}"
            except:
                continue

        return "Content not available (paywalled)"

    return "Content not available"


def scrape_article(driver, url, index=0, test_run_id=None):
    try:
        driver.set_page_load_timeout(60)
        driver.get(url)
    except Exception:
        print(f"[SCRAPER] Page load timeout for article {index} — using partial content")

    time.sleep(2)

    # ✅ Dismiss cookie banner on EVERY article page
    accept_cookies(driver)

    # Give page time to settle after dismissing banner
    time.sleep(2)

    # ── Title & Content ───────────────────────────────────────
    title   = _extract_title(driver, index)
    content = _extract_content(driver, index)

    # ── Image ─────────────────────────────────────────────────
    image_url = local_path = supabase_url = None
    try:
        img       = driver.find_element(By.CSS_SELECTOR, "figure img, article img")
        image_url = img.get_attribute("src")
    except:
        pass

    if image_url:
        local_path = download_image(image_url, index)
        if local_path:
            storage_result = save_and_upload_image(local_path, f"article_{index}.jpg")
            supabase_url   = storage_result["supabase_url"]

    # ── DB Save ───────────────────────────────────────────────
    article_data = {
        "title":            title,
        "content":          content,
        "image_url":        supabase_url or image_url or "",
        "image_local_path": local_path or "",
        "article_url":      url,
        "test_run_id":      test_run_id,
    }

    db_record = {}
    if test_run_id:
        db_record = db.save_article(article_data)

    return {
        **article_data,
        "db_id": db_record.get("id") if db_record else None,
    }