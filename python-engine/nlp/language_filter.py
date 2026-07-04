# ============================================================
# nlp/language_filter.py
# Filters out non-English content using the langdetect library
# ============================================================

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def is_english(text: str) -> bool:
    """
    Detects if the text is English. Returns True if English, False otherwise.
    """
    if not text or not text.strip():
        return False
    try:
        # Detect primary language code (e.g., 'en')
        lang = detect(text)
        return lang == "en"
    except LangDetectException:
        # Fallback to False if language cannot be detected
        return False


def filter_english_documents(documents: list[dict]) -> list[dict]:
    """
    Filters a list of documents, keeping only those detected as English.
    """
    filtered = []
    for doc in documents:
        text = doc.get("text", "")
        if is_english(text):
            filtered.append(doc)
    
    print(f"[LanguageFilter] Kept {len(filtered)}/{len(documents)} English documents.")
    return filtered
