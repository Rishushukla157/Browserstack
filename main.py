from concurrent.futures import ThreadPoolExecutor, as_completed
from browser.driver_factory import get_local_driver
from scraping.elpais_scraper import get_opinion_article_links, scrape_article
from translation.translator import translate_to_english, translate_content
from analysis.text_analyzer import find_repeated_words_raw, find_repeated_words_semantic
from utils.output_writer import save_json
from backend.database import db
import threading

# ┌──────────────────────────────────────────────┐
# │  🔧 TOGGLE MODE HERE                         │
# │  True  = Multithreaded (fast, parallel)      │
# │  False = Sequential    (slow, 1 browser)     │
# └──────────────────────────────────────────────┘
USE_MULTITHREADING =  False

db_lock = threading.Lock()


def process_article(idx, link, test_run_id, driver=None):
    """
    Sequential mode : driver is passed in → reused, NOT quit after
    Multithreaded   : driver=None → creates its own, quits after
    """
    own_driver = driver is None      # did THIS call create the driver?
    if own_driver:
        driver = get_local_driver()  # each thread gets its own

    try:
        print(f"[THREAD] 🚀 Starting article {idx + 1}")

        data    = scrape_article(driver, link, index=idx + 1, test_run_id=test_run_id)
        title   = data["title"]   or "No title found"
        content = data["content"] or "No content found"

        # ── Translate Title ───────────────────────────────────
        translated_title = ""
        if data["title"]:
            translated_title = translate_to_english(data["title"])
            if data.get("db_id") and translated_title:
                with db_lock:
                    db.update_article_translation(data["db_id"], translated_title)

        # ── Translate Content ─────────────────────────────────
        translated_content = ""
        if content and content not in ("No content found", "Content not available", "Content not available (paywalled)"):
            print(f"[TRANSLATOR] Translating content for article {idx + 1}...")
            translated_content = translate_content(content)
            if data.get("db_id") and translated_content:
                with db_lock:
                    db.update_article_content_translation(data["db_id"], translated_content)

        print(f"\n📰 ARTICLE {idx + 1}")
        print(f"  Spanish Title   : {title}")
        print(f"  English Title   : {translated_title or 'N/A'}")
        print(f"\n  Spanish Content : {content[:200]}...")
        print(f"  English Content : {translated_content[:200]}..." if translated_content else "  English Content : N/A")

        return {
            "idx":             idx,
            "spanish_title":   title,
            "english_title":   translated_title,
            "spanish_content": content,
            "english_content": translated_content,
            "image_url":       data.get("image_url", ""),
        }

    finally:
        if own_driver:
            driver.quit()  # only quit if THIS call created it


# ── Sequential: 1 browser, navigates article to article ───────
def _run_sequential(links, test_run_id, driver):
    print("[PIPELINE] 🐢 Mode: Sequential (1 browser reused)")
    results = []
    for idx, link in enumerate(links):
        print(f"\n{'='*50}\nProcessing article {idx + 1}")
        try:
            # ✅ Pass shared driver → no new window opens
            results.append(process_article(idx, link, test_run_id, driver=driver))
        except Exception as e:
            print(f"[PIPELINE] ❌ Article {idx + 1} failed: {e}")
    return results


# ── Multithreaded: 5 browsers simultaneously ──────────────────
def _run_multithreaded(links, test_run_id):
    print("[PIPELINE] ⚡ Mode: Multithreaded (1 browser per thread)")
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            # ✅ No driver passed → each thread creates & quits its own
            executor.submit(process_article, idx, link, test_run_id): idx
            for idx, link in enumerate(links)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results.append(future.result())
                print(f"[PIPELINE] ✅ Article {idx + 1} complete")
            except Exception as e:
                print(f"[PIPELINE] ❌ Article {idx + 1} failed: {e}")

    results.sort(key=lambda x: x["idx"])
    return results


def run_pipeline(driver, test_run_id=None):
    links = get_opinion_article_links(driver)
    print(f"Found {len(links)} articles")

    if USE_MULTITHREADING:
        # Main driver only used for link collection above
        results = _run_multithreaded(links, test_run_id)
    else:
        # ✅ Pass same driver → single window, no new tabs
        results = _run_sequential(links, test_run_id, driver)

    translated_titles = [r["english_title"] for r in results if r["english_title"]]
    raw_result      = find_repeated_words_raw(translated_titles,      test_run_id=test_run_id)
    semantic_result = find_repeated_words_semantic(translated_titles, test_run_id=test_run_id)

    print(f"\n{'='*50}")
    print("RAW REPEATED WORDS (>2 times):")
    if raw_result:
        for word, count in raw_result.items():
            print(f"  {word} → {count}")
    else:
        print("  No words repeated more than twice.")

    print("\nSEMANTIC REPEATED WORDS (>2 times):")
    if semantic_result:
        for word, count in semantic_result.items():
            print(f"  {word} → {count}")
    else:
        print("  No words repeated more than twice.")

    save_json([{k: v for k, v in r.items() if k != "idx"} for r in results])


if __name__ == "__main__":
    test_run = db.create_test_run(browser="chrome", platform="local", session_id="local-run")
    run_id   = test_run.get("id", None)
    driver   = get_local_driver()
    try:
        run_pipeline(driver, test_run_id=run_id)
        if run_id:
            db.update_test_run_status(run_id, "passed")
        print(f"\n✅ Pipeline completed successfully")
    except Exception as e:
        if run_id:
            db.update_test_run_status(run_id, "failed")
        print(f"\n❌ Pipeline failed: {e}")
        raise
    finally:
        driver.quit()