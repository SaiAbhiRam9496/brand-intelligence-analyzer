# ============================================================
# nlp/sentiment.py
# Sentiment analysis on collected documents (News + YouTube)
# - VADER for short texts (titles, headlines)
# - DistilBERT for longer texts (full descriptions/articles)
# Output per document: label (Positive/Negative/Neutral) + confidence
# ============================================================

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# ── Constants ───────────────────────────────────────────────
SHORT_TEXT_WORD_THRESHOLD = 25  # Below this word count → use VADER

# ── Initialize models once (expensive to load) ────────────────
_vader_analyzer = SentimentIntensityAnalyzer()
_distilbert_pipeline = None  # Lazy-loaded on first use


def _get_distilbert_pipeline():
    """
    Lazy-loads DistilBERT only when first needed.
    First call downloads the model (~260MB) and caches it locally.
    """
    global _distilbert_pipeline
    if _distilbert_pipeline is None:
        print("[Sentiment] Loading DistilBERT model (first run downloads ~260MB)...")
        _distilbert_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
        print("[Sentiment] DistilBERT loaded.")
    return _distilbert_pipeline


# ── VADER Analysis (short text) ────────────────────────────────
def _analyze_with_vader(text: str) -> dict:
    """
    Runs VADER sentiment analysis. Best for short, informal text
    like headlines and social media style content.
    """
    scores = _vader_analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    # Use absolute compound score as confidence (0 to 1 scale)
    confidence = abs(compound)

    return {"label": label, "confidence": round(confidence, 3), "model_used": "VADER"}


# ── DistilBERT Analysis (longer text) ──────────────────────────
def _analyze_with_distilbert(text: str) -> dict:
    """
    Runs DistilBERT sentiment analysis. Best for longer, more
    nuanced text like full article descriptions.
    Note: DistilBERT SST-2 only outputs POSITIVE/NEGATIVE (no neutral),
    so we treat low-confidence results as Neutral.
    """
    try:
        clf = _get_distilbert_pipeline()
        result = clf(text[:2000])[0]  # Truncate very long text for speed

        raw_label = result["label"]  # "POSITIVE" or "NEGATIVE"
        score = result["score"]

        # If confidence is low, treat as Neutral (model is unsure)
        if score < 0.6:
            label = "Neutral"
        else:
            label = "Positive" if raw_label == "POSITIVE" else "Negative"

        return {"label": label, "confidence": round(score, 3), "model_used": "DistilBERT"}

    except Exception as e:
        print(f"[Sentiment] DistilBERT failed, falling back to VADER: {e}")
        return _analyze_with_vader(text)


# ── Main Function — Analyze Single Document ────────────────────
def analyze_sentiment(text: str) -> dict:
    """
    Routes text to the appropriate sentiment model based on length.
    Short text (headlines) → VADER
    Long text (articles/descriptions) → DistilBERT

    Returns: {"label": "Positive"/"Negative"/"Neutral", "confidence": float, "model_used": str}
    """
    if not text or not text.strip():
        return {"label": "Neutral", "confidence": 0.0, "model_used": "none"}

    word_count = len(text.split())

    if word_count <= SHORT_TEXT_WORD_THRESHOLD:
        return _analyze_with_vader(text)
    else:
        return _analyze_with_distilbert(text)


# ── Batch Function — Analyze List of Documents ─────────────────
def analyze_documents(documents: list[dict]) -> list[dict]:
    """
    Takes a list of document dicts (from collectors) and adds
    sentiment analysis results to each one.

    Args:
        documents: list of dicts, each must have a "text" field

    Returns:
        Same list, with each dict updated to include "sentiment" field
    """
    print(f"[Sentiment] Analyzing {len(documents)} documents...")

    for i, doc in enumerate(documents):
        text = doc.get("text", "")
        result = analyze_sentiment(text)
        doc["sentiment"] = result["label"]
        doc["sentiment_confidence"] = result["confidence"]
        doc["sentiment_model"] = result["model_used"]

        if (i + 1) % 25 == 0:
            print(f"[Sentiment] Processed {i + 1}/{len(documents)}")

    print(f"[Sentiment] Done. {len(documents)} documents analyzed.")
    return documents


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_texts = [
        "I absolutely love this product, best purchase ever!",
        "This is the worst customer service I've ever experienced.",
        "The company released its quarterly earnings report today.",
        "Nike CEO Talks Coming out of Retirement to Revive Brand",
        "Customers are suing Nike and others over IEEPA tariff refunds. The companies are facing lawsuits as refund payments begin to roll out.",
    ]

    for text in test_texts:
        result = analyze_sentiment(text)
        print(f"\nText: {text[:80]}")
        print(f"→ {result}")