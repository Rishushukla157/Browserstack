from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import requests
import time
import random

OPINION_URL = "https://elpais.com/opinion/"


# ── Random Sleep ───────────────────────
def random_sleep(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


# ── Helper ─────────────────────────────
def get_soup(driver):
    return BeautifulSoup(driver.page_source, "html.parser")


# ── Cookies ────────────────────────────
def accept_cookies(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#didomi-notice-agree-button"))
        )
        btn.click()
        random_sleep(0.5, 1.5)
    except:
        pass


# ── Download Image ─────────────────────
def download_image(url, index):
    os.makedirs("output_images", exist_ok=True)
    path = f"output_images/article_{index}.jpg"

    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            with open(path, "wb") as f:
                f.write(res.content)
            print(f"[IMAGE] Saved locally → {path}")
            return path
    except:
        pass

    return ""


# ── Extract Image (FIXED) ──────────────
def extract_image(soup):
    selectors = [
        "figure img",
        "article img",
        "img"
    ]

    for sel in selectors:
        img = soup.select_one(sel)
        if not img:
            continue

        # Try all attributes
        if img.get("src") and img["src"].startswith("http"):
            return img["src"]

        if img.get("data-src"):
            return img["data-src"]

        if img.get("srcset"):
            return img["srcset"].split(",")[-1].split()[0]

        if img.get("data-srcset"):
            return img["data-srcset"].split(",")[-1].split()[0]

    return None


# ── Extract Title ──────────────────────
def extract_title(soup):
    title = soup.select_one("h1")
    return title.get_text(strip=True) if title else ""


# ── Extract Content (WITH PAYWALL FIX) ─
def extract_content(soup, index):
    container = soup.select_one("article")

    if container:
        paragraphs = container.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if text:
            return text

    # 🔥 Paywall detection
    page_text = soup.get_text().lower()
    if "suscri" in page_text:
        subtitle = soup.select_one("h2, p")
        if subtitle:
            return "[Paywalled — preview only] " + subtitle.get_text(strip=True)

    return ""


# ── Get Links ──────────────────────────
def get_opinion_article_links(driver, max_links=5):
    driver.get(OPINION_URL)
    random_sleep()

    accept_cookies(driver)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "article h2 a"))
    )

    soup = get_soup(driver)
    anchors = soup.select("article h2 a")

    links = []
    for a in anchors:
        href = a.get("href")
        if href and href.startswith("/"):
            href = "https://elpais.com" + href
        if href and "/opinion/" in href:
            links.append(href)
        if len(links) == max_links:
            break

    return links


# ── Main Scraper ───────────────────────
def scrape_article(driver, url, index=0):
    print(f"[THREAD] 🚀 Starting article {index}")

    driver.get(url)
    random_sleep()

    accept_cookies(driver)
    random_sleep()

    soup = get_soup(driver)

    title = extract_title(soup)
    content = extract_content(soup, index)

    # ✅ FIXED IMAGE PART
    image_url = extract_image(soup)
    image_local_path = ""

    if image_url:
        print(f"[IMAGE] Found → {image_url}")
        image_local_path = download_image(image_url, index)

    print(f"[SCRAPER] ✅ Article {index} done — '{title[:50]}'")
    random_sleep()

    return {
        "title": title,
        "content": content,
        "image_url": image_url or "",
        "image_local_path": image_local_path,
        "article_url": url,
    }