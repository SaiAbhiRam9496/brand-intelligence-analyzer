# ============================================================
# nlp/text_cleaning.py
# Text cleaning utilities — run BEFORE keyword extraction
# and topic modeling (per the brief's Step 1: Text Cleaning)
# Removes URLs, emojis, hashtags, promo codes, special chars
# ============================================================

import re

# ── Regex Patterns ──────────────────────────────────────────
URL_PATTERN = re.compile(r"http\S+|www\.\S+")
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE
)
HASHTAG_PATTERN = re.compile(r"#\w+")
PROMO_CODE_PATTERN = re.compile(r"\buse\s+code\s*:?\s*[A-Z0-9]{3,15}\b|\b(code|promo)\s*:?\s*[A-Z0-9]{3,15}\b", re.IGNORECASE)
EXTRA_WHITESPACE_PATTERN = re.compile(r"\s+")
SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s.,!?'-]")
HTML_ENTITY_PATTERN = re.compile(r"&[a-zA-Z]+;|&#\d+;")


# ── Main Cleaning Function ─────────────────────────────────────
def clean_text(text: str) -> str:
    """
    Cleans a single text string for NLP processing.
    Removes URLs, emojis, hashtags, promo codes, HTML entities,
    and normalizes whitespace. Keeps basic punctuation for
    sentence structure (sentiment models benefit from this).
    """
    if not text:
        return ""

    text = HTML_ENTITY_PATTERN.sub(" ", text)
    text = URL_PATTERN.sub(" ", text)
    text = EMOJI_PATTERN.sub(" ", text)
    text = HASHTAG_PATTERN.sub(" ", text)
    text = PROMO_CODE_PATTERN.sub(" ", text)
    text = SPECIAL_CHARS_PATTERN.sub(" ", text)
    text = EXTRA_WHITESPACE_PATTERN.sub(" ", text)

    return text.strip()


# ── Batch Cleaning Function ────────────────────────────────────
def clean_documents(documents: list[dict]) -> list[dict]:
    """
    Cleans the 'text' field of each document in place.
    Stores original text as 'raw_text' for reference if needed.
    """
    for doc in documents:
        original = doc.get("text", "")
        doc["raw_text"] = original
        doc["text"] = clean_text(original)

    return documents


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        "my *EXPENSIVE* birthday gift to myself!🤯😱 #minivlog #nikeshoes",
        "Check out https://example.com for more! Use code: SAVE20 now!!!",
        "Nike&#39;s $1 Billion Headquarters tour — exclusive access 🏢✨",
        "LISA x NikeSKIMS Spring `26 Collection | Nike #fashion #style",
    ]

    for text in test_cases:
        cleaned = clean_text(text)
        print(f"Before: {text}")
        print(f"After:  {cleaned}\n")