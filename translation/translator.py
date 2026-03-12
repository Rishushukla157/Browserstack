import requests
from config.settings import TRANSLATE_API_KEY, TRANSLATE_API_URL


def translate_to_english(text):
    """Translates a single text from Spanish to English."""
    if not text or not text.strip():
        return ""

    if not TRANSLATE_API_KEY:
        print("[TRANSLATOR] No API key set — skipping translation")
        return text

    try:
        response = requests.post(
            TRANSLATE_API_URL,
            params={"key": TRANSLATE_API_KEY},
            json={
                "q":      text,
                "source": "es",
                "target": "en",
                "format": "text",
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            return data["data"]["translations"][0]["translatedText"]
        else:
            print(f"[TRANSLATOR] API error: {response.status_code}")
            return text

    except Exception as e:
        print(f"[TRANSLATOR] Error: {e}")
        return text


def translate_content(text):
    """
    Translates long article content.
    Google Translate API has a 5000 char limit per request
    so we split long content into chunks.
    """
    if not text or not text.strip():
        return ""

    if text == "Content not available":
        return "Content not available"

    CHUNK_SIZE = 4500  # stay safely under 5000 char limit

    # If content is short enough — translate in one call
    if len(text) <= CHUNK_SIZE:
        return translate_to_english(text)

    # Split into chunks and translate each one
    chunks     = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    translated = []

    for i, chunk in enumerate(chunks):
        print(f"[TRANSLATOR] Translating content chunk {i+1}/{len(chunks)}...")
        result = translate_to_english(chunk)
        translated.append(result)

    return " ".join(translated)