from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Download required NLTK data (run once)
nltk.download('stopwords')
nltk.download('punkt')


def process_headers(headers, use_stopwords=False, threshold=2):
    # 1. Remove empty headers
    valid_headers = [h for h in headers if h]

    if not valid_headers:
        return {}

    # 2. Combine + lowercase
    combined = " ".join(valid_headers).lower()

    # 3. Tokenize
    tokens = word_tokenize(combined)

    # 4. Remove punctuation
    tokens = [t for t in tokens if t not in string.punctuation]

    # 5. Remove very short words (noise filter 🔥)
    tokens = [t for t in tokens if len(t) > 2]

    # 6. Remove stopwords (semantic mode)
    if use_stopwords:
        stop_words = set(stopwords.words('english'))
        tokens = [t for t in tokens if t not in stop_words]

    # 7. Count words
    word_counts = Counter(tokens)

    # 8. Keep words repeated ≥ threshold ✅ FIXED
    repeated_words = {
        word: count for word, count in word_counts.items()
        if count >= threshold
    }

    return repeated_words


# ── MAIN FUNCTION ──────────────────────
def find_repeated_words(headers, threshold=2):
    
    print("\n🔍 RAW REPEATED WORDS (>=2 times):")
    raw = process_headers(headers, use_stopwords=False, threshold=threshold)

    if raw:
        for word, count in raw.items():
            print(f"  {word} → {count}")
    else:
        print("  None")

    print("\n🧠 SEMANTIC REPEATED WORDS (>=2 times):")
    semantic = process_headers(headers, use_stopwords=True, threshold=threshold)

    if semantic:
        for word, count in semantic.items():
            print(f"  {word} → {count}")
    else:
        print("  None")

    return raw, semantic