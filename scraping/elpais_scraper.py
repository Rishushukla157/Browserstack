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
        time.sleep(1)
    except:
        pass


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


def scrape_article(driver, url, index=0, test_run_id=None):
    # ── Load page with timeout protection ───────────────────
    try:
        driver.set_page_load_timeout(60)
        driver.get(url)
    except Exception:
        print(f"[SCRAPER] Page load timeout for article {index} — using partial content")

    time.sleep(2)

    wait = WebDriverWait(driver, 20)

    # ── Title ────────────────────────────────────────────────
    title = ""
    try:
        title_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1.a_t, h1[class*='title'], article h1")
            )
        )
        title = title_el.text.strip()
    except:
        print(f"[SCRAPER] Title not found for article {index}")

    # ── Content ──────────────────────────────────────────────
    content = ""
    try:
        content_selectors = [
            "div[data-dtm-region='articulo_cuerpo']",
            "div.a_c",
            "article div.article-body",
            "div.article_body"
        ]
        for selector in content_selectors:
            try:
                container  = driver.find_element(By.CSS_SELECTOR, selector)
                paragraphs = container.find_elements(By.TAG_NAME, "p")
                content    = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
                if content:
                    break
            except:
                continue

        if not content:
            paragraphs = driver.find_elements(By.CSS_SELECTOR, "article p")
            content    = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

        if not content:
            content = "Content not available"

    except Exception as e:
        print(f"[SCRAPER] Content not found for article {index}: {e}")
        content = "Content not available"

    # ── Image ─────────────────────────────────────────────────
    image_url    = None
    local_path   = None
    supabase_url = None

    try:
        img       = driver.find_element(By.CSS_SELECTOR, "figure img, article img")
        image_url = img.get_attribute("src")
    except:
        pass

    if image_url:
        # Save locally first
        local_path = download_image(image_url, index)

        # Then upload to Supabase Storage
        if local_path:
            storage_result = save_and_upload_image(local_path, f"article_{index}.jpg")
            supabase_url   = storage_result["supabase_url"]

    # ── Save to Supabase DB ───────────────────────────────────
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
