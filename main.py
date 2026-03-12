from browser.driver_factory import get_local_driver
from scraping.elpais_scraper import get_opinion_article_links, scrape_article
from translation.translator import translate_to_english, translate_content
from utils.image_downloader import download_image
from analysis.text_analyzer import find_repeated_words_raw, find_repeated_words_semantic
from utils.output_writer import save_json
from backend.database import db


def run_pipeline(driver, test_run_id=None):
    links = get_opinion_article_links(driver)
    print(f"Found {len(links)} articles")

    results           = []
    translated_titles = []

    for idx, link in enumerate(links):
        print(f"\n{'='*50}")
        print(f"Processing article {idx + 1}")

        data = scrape_article(driver, link, index=idx + 1, test_run_id=test_run_id)

        title   = data["title"]   or "No title found"
        content = data["content"] or "No content found"

        translated_title = ""
        if data["title"]:
            translated_title = translate_to_english(data["title"])
            if data.get("db_id") and translated_title:
                db.update_article_translation(data["db_id"], translated_title)

        translated_content = ""
        if content and content != "No content found":
            print(f"[TRANSLATOR] Translating content for article {idx + 1}...")
            translated_content = translate_content(content)
            if data.get("db_id") and translated_content:
                db.update_article_content_translation(data["db_id"], translated_content)

        print(f"\n📰 ARTICLE {idx + 1}")
        print(f"  Spanish Title   : {title}")
        print(f"  English Title   : {translated_title or 'N/A'}")
        print(f"\n  Spanish Content : {content[:200]}...")
        print(f"  English Content : {translated_content[:200]}..." if translated_content else "  English Content : N/A")

        results.append({
            "spanish_title":   title,
            "english_title":   translated_title,
            "spanish_content": content,
            "english_content": translated_content,
            "image_url":       data.get("image_url", ""),
        })

        if translated_title:
            translated_titles.append(translated_title)

    raw_result      = find_repeated_words_raw(translated_titles,      test_run_id=test_run_id)
    semantic_result = find_repeated_words_semantic(translated_titles, test_run_id=test_run_id)

    print(f"\n{'='*50}")
    print("RAW REPEATED WORDS (>2 times):")
    if raw_result:
        for word, count in raw_result.items():
            print(f"  {word} → {count}")
    else:
        print("  No words repeated more than twice.")

    print("\nSEMANTIC REPEATED WORDS (>2 times, stopwords removed):")
    if semantic_result:
        for word, count in semantic_result.items():
            print(f"  {word} → {count}")
    else:
        print("  No words repeated more than twice.")

    save_json(results)


if __name__ == "__main__":
    test_run = db.create_test_run(
        browser="chrome",
        platform="local",
        session_id="local-run"
    )
    run_id = test_run.get("id", None)

    driver = get_local_driver()
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