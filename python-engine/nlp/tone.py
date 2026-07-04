# ============================================================
# nlp/tone.py
# Tone detection using HuggingFace zero-shot classification
# Runs on the brand's Wikipedia text to detect overall tone
# Reveals how the brand is described vs how public perceives it
# ============================================================

from transformers import pipeline

# ── Constants ───────────────────────────────────────────────
TONE_CATEGORIES = [
    "Professional",
    "Casual",
    "Aggressive",
    "Inspirational",
    "Fear-based",
    "Humorous",
]

MAX_INPUT_CHARS = 2000  # Zero-shot classification works best on shorter text

# ── Initialize model once (lazy-loaded) ────────────────────────
_zero_shot_pipeline = None


def _get_zero_shot_pipeline():
    """
    Lazy-loads the zero-shot classification pipeline.
    Uses facebook/bart-large-mnli, the standard model for this task.
    """
    global _zero_shot_pipeline
    if _zero_shot_pipeline is None:
        print("[Tone] Loading zero-shot classification model (first run downloads ~1.6GB)...")
        _zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        print("[Tone] Zero-shot model loaded.")
    return _zero_shot_pipeline


# ── Main Function — Detect Tone ────────────────────────────────
def detect_tone(text: str) -> dict:
    """
    Classifies text into tone categories using zero-shot classification.
    Returns scores for all categories, sorted highest to lowest.

    Args:
        text: Brand text to analyze (e.g. Wikipedia general_text)

    Returns:
        Dict with "primary_tone", "all_scores" (list of {tone, score})
    """
    if not text or not text.strip():
        return {"primary_tone": "Unknown", "all_scores": []}

    # Cap input length for performance
    text = text[:MAX_INPUT_CHARS]

    print(f"[Tone] Classifying tone from {len(text.split())} words of text...")

    classifier = _get_zero_shot_pipeline()
    result = classifier(text, candidate_labels=TONE_CATEGORIES, multi_label=True)

    # result has 'labels' and 'scores', already sorted by score descending
    all_scores = [
        {"tone": label, "score": round(score, 4)}
        for label, score in zip(result["labels"], result["scores"])
    ]

    primary_tone = all_scores[0]["tone"] if all_scores else "Unknown"

    print(f"[Tone] Primary tone detected: {primary_tone}")

    return {
        "primary_tone": primary_tone,
        "all_scores": all_scores,
    }


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_text = (
        "Nike's mission is to bring inspiration and innovation to every athlete in the world. "
        "We believe if you have a body, you are an athlete. Our purpose is to move the world forward "
        "through the power of sport — breaking barriers and pushing the limits of what's possible."
    )

    result = detect_tone(test_text)
    print("\nAll tone scores:")
    for item in result["all_scores"]:
        print(f"  {item['tone']}: {item['score']}")
    print(f"\nPrimary tone: {result['primary_tone']}")