from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Download required NLTK data (run once)
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')


def _process_headers(headers, use_stopwords=False, threshold=2):
    """
    Private helper — shared logic between both functions.
    Avoids code duplication.
    """
    # 1. Filter out None values
    valid_headers = [h for h in headers if h is not None]
    if not valid_headers:
        return {}

    # 2. Combine all headers into one string
    combined = " ".join(valid_headers).lower()

    # 3. NLTK tokenizer — handles punctuation, contractions, special chars
    #    e.g. "price," → "price"  |  "it's" → "it", "'s"
    tokens = word_tokenize(combined)

    # 4. Strip out pure punctuation tokens like ".", ",", "!", "--"
    tokens = [t for t in tokens if t not in string.punctuation]

    # 5. Optionally remove stopwords using NLTK's built-in list
    #    NLTK has 179 English stopwords vs our old hardcoded ~20
    if use_stopwords:
        stop_words = set(stopwords.words('english'))
        tokens = [t for t in tokens if t not in stop_words]

    # 6. Count and filter by threshold
    word_counts = Counter(tokens)
    return {word: count for word, count in word_counts.items() if count > threshold}


def find_repeated_words_raw(headers, threshold=2):
    return _process_headers(headers, use_stopwords=False, threshold=threshold)


def find_repeated_words_semantic(headers, threshold=2):
    return _process_headers(headers, use_stopwords=True, threshold=threshold)