# ============================================================
# nlp/keywords.py
# Keyword extraction using KeyBERT
# Runs on all collected text combined to find top keywords
# associated with the brand across all sources
# ============================================================

from keybert import KeyBERT

# ── Constants ───────────────────────────────────────────────
TOP_N_KEYWORDS = 25
KEYPHRASE_NGRAM_RANGE = (1, 2)  # Single words and two-word phrases
MAX_INPUT_WORDS = 5000  # Cap combined text length for performance

# ── Initialize model once (lazy-loaded) ────────────────────────
_keybert_model = None


def _get_keybert_model():
    """
    Lazy-loads KeyBERT model only when first needed.
    Uses the default underlying sentence-transformer model.
    """
    global _keybert_model
    if _keybert_model is None:
        print("[Keywords] Loading KeyBERT model (first run downloads embedding model)...")
        _keybert_model = KeyBERT()
        print("[Keywords] KeyBERT loaded.")
    return _keybert_model


# ── Main Function — Extract Keywords ───────────────────────────
def extract_keywords(documents: list[dict], top_n: int = TOP_N_KEYWORDS) -> list[dict]:
    """
    Combines all document text and extracts top keywords using KeyBERT.

    Args:
        documents: list of dicts, each must have a "text" field
        top_n: number of keywords to return

    Returns:
        List of dicts: [{"keyword": "...", "score": 0.45}, ...]
        Sorted by relevance score, highest first.
    """
    if not documents:
        print("[Keywords] No documents provided.")
        return []

    # Combine all text into one block
    combined_text = " ".join(doc.get("text", "") for doc in documents)
    combined_text = combined_text.strip()

    if not combined_text:
        print("[Keywords] Combined text is empty.")
        return []

    # Cap length for performance — keyword signal saturates well before this
    words = combined_text.split()
    if len(words) > MAX_INPUT_WORDS:
        combined_text = " ".join(words[:MAX_INPUT_WORDS])

    print(f"[Keywords] Extracting top {top_n} keywords from {len(words)} words of combined text...")

    model = _get_keybert_model()

    raw_keywords = model.extract_keywords(
        combined_text,
        keyphrase_ngram_range=KEYPHRASE_NGRAM_RANGE,
        stop_words="english",
        top_n=top_n,
        use_mmr=True,       # Maximal Marginal Relevance — reduces redundant similar keywords
        diversity=0.5,      # Balance between relevance and diversity
    )

    results = [{"keyword": kw, "score": round(score, 4)} for kw, score in raw_keywords]

    print(f"[Keywords] Extracted {len(results)} keywords.")
    return results


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_documents = [
        {"text": "Nike releases new sustainable sneaker line made from recycled materials."},
        {"text": "Customers complain about Nike's customer service and slow shipping times."},
        {"text": "Nike's marketing campaign featuring top athletes goes viral on social media."},
        {"text": "Lawsuit filed against Nike over labor practices in overseas factories."},
        {"text": "Nike stock price rises after strong quarterly earnings report."},
    ]

    keywords = extract_keywords(test_documents, top_n=10)
    print("\nTop keywords:")
    for kw in keywords:
        print(f"  {kw['keyword']}: {kw['score']}")