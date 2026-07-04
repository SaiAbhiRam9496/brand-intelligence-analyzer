# ============================================================
# nlp/topics.py
# Dynamic topic modeling on negative-sentiment documents using BERTopic
# Adapts clustering strategy based on document volume to avoid failures
# ============================================================

from bertopic import BERTopic
from sklearn.cluster import KMeans
import pandas as pd

MAX_TOPICS_TO_SHOW = 10


def model_negative_topics(documents: list[dict]) -> dict:
    """
    Groups negative documents into clusters to reveal common complaints/topics.
    Uses dynamic clustering (KMeans vs HDBSCAN) based on document volume.
    """
    negative_docs = [doc for doc in documents if doc.get("sentiment") == "Negative"]
    negative_count = len(negative_docs)

    print(f"[Topics] Found {negative_count} negative documents for topic modeling.")

    # 1. Volume Gate: < 15 docs is too low for BERTopic
    if negative_count < 15:
        return {
            "status": "skipped",
            "reason": (
                f"Insufficient negative data for clustering. "
                f"Found {negative_count} negative items (minimum 15 required)."
            ),
            "negative_doc_count": negative_count,
            "topics": [],
        }

    texts = [doc["text"] for doc in negative_docs if doc.get("text", "").strip()]

    try:
        # 2. Dynamic Clustering selection
        if negative_count < 100:
            # Low volume: Use KMeans with 3-4 clusters to guarantee clusters
            num_clusters = min(4, max(2, negative_count // 5))
            print(f"[Topics] Low volume ({negative_count} docs). Using KMeans with K={num_clusters}.")
            cluster_model = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
            topic_model = BERTopic(hdbscan_model=cluster_model, verbose=False)
        else:
            # High volume: Use default HDBSCAN
            print(f"[Topics] High volume ({negative_count} docs). Using default HDBSCAN.")
            topic_model = BERTopic(min_topic_size=max(5, min(10, negative_count // 20)), verbose=False)

        topics, probs = topic_model.fit_transform(texts)
        topic_info = topic_model.get_topic_info()

        results = []
        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]

            # Outlier cluster (-1) from HDBSCAN is skipped
            if topic_id == -1:
                continue

            keywords = [word for word, _ in topic_model.get_topic(topic_id)][:6]
            label = ", ".join(keywords[:3])

            results.append({
                "topic_id": int(topic_id),
                "label": label,
                "keywords": keywords,
                "document_count": int(row["Count"]),
            })

            if len(results) >= MAX_TOPICS_TO_SHOW:
                break

        print(f"[Topics] Extracted {len(results)} negative topic clusters.")
        return {
            "status": "success",
            "negative_doc_count": negative_count,
            "topics": results,
        }

    except Exception as e:
        print(f"[Topics] Error during BERTopic modeling: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "negative_doc_count": negative_count,
            "topics": [],
        }