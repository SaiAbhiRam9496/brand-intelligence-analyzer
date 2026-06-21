# ============================================================
# nlp/topics.py
# Topic modeling on negative-sentiment documents using BERTopic
# Reveals root causes behind negative brand sentiment
# Requires minimum 300 negative documents — skips with a clear
# warning if threshold isn't met (per project scope rules)
# ============================================================

from bertopic import BERTopic

# ── Constants ───────────────────────────────────────────────
MIN_NEGATIVE_DOCS = 300  # Threshold from project brief
MAX_TOPICS_TO_SHOW = 10  # Top N topics to return, excluding outliers


# ── Main Function — Topic Modeling ─────────────────────────────
def model_negative_topics(documents: list[dict]) -> dict:
    """
    Filters documents to only Negative-sentiment ones, then runs
    BERTopic to find clusters of negative content (root causes).

    Args:
        documents: list of dicts, each must have "text" and "sentiment" fields
                   (output of nlp.sentiment.analyze_documents)

    Returns:
        Dict with either:
        - {"status": "skipped", "reason": "...", "negative_doc_count": N}
        - {"status": "success", "topics": [...], "negative_doc_count": N}
    """
    negative_docs = [doc for doc in documents if doc.get("sentiment") == "Negative"]
    negative_count = len(negative_docs)

    print(f"[Topics] Found {negative_count} negative documents "
          f"(need {MIN_NEGATIVE_DOCS} minimum for topic modeling)")

    if negative_count < MIN_NEGATIVE_DOCS:
        return {
            "status": "skipped",
            "reason": (
                f"Insufficient negative documents for reliable topic modeling. "
                f"Found {negative_count}, need at least {MIN_NEGATIVE_DOCS}. "
                f"This is common for brands without major recent controversies — "
                f"sentiment and keyword analysis are still fully valid."
            ),
            "negative_doc_count": negative_count,
            "topics": [],
        }

    texts = [doc["text"] for doc in negative_docs if doc.get("text", "").strip()]

    print(f"[Topics] Running BERTopic on {len(texts)} negative documents...")

    try:
        topic_model = BERTopic(min_topic_size=10, verbose=False)
        topics, probs = topic_model.fit_transform(texts)

        topic_info = topic_model.get_topic_info()

        results = []
        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]

            # Topic -1 is BERTopic's "outlier" bucket — skip it
            if topic_id == -1:
                continue

            keywords = [word for word, _ in topic_model.get_topic(topic_id)][:6]
            label = ", ".join(keywords[:3])  # Simple auto-label from top keywords

            results.append({
                "topic_id": int(topic_id),
                "label": label,
                "keywords": keywords,
                "document_count": int(row["Count"]),
            })

            if len(results) >= MAX_TOPICS_TO_SHOW:
                break

        print(f"[Topics] Found {len(results)} distinct negative topics.")

        return {
            "status": "success",
            "negative_doc_count": negative_count,
            "topics": results,
        }

    except Exception as e:
        print(f"[Topics] BERTopic failed: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "negative_doc_count": negative_count,
            "topics": [],
        }


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate a small dataset (below threshold) to test the skip logic
    small_docs = [
        {"text": "Delivery was very late and customer service was unhelpful.", "sentiment": "Negative"},
        {"text": "The product broke after one week of use, terrible quality.", "sentiment": "Negative"},
        {"text": "Great experience overall, very happy with my purchase.", "sentiment": "Positive"},
    ]

    result = model_negative_topics(small_docs)
    print("\nResult:", result)