# ============================================================
# nlp/topics.py
# Dynamic topic modeling on negative-sentiment documents using BERTopic
# Adapts clustering strategy based on document volume to avoid failures.
# Includes a TF-IDF + KMeans fallback if BERTopic/sentence_transformers fails.
# ============================================================

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
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
        from bertopic import BERTopic
        
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
        
        topic_to_docs = {}
        for idx, topic_id in enumerate(topics):
            topic_to_docs.setdefault(int(topic_id), []).append(negative_docs[idx])
            
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
                "documents": topic_to_docs.get(int(topic_id), []),
            })

            if len(results) >= MAX_TOPICS_TO_SHOW:
                break

        print(f"[Topics] Extracted {len(results)} negative topic clusters using BERTopic.")
        return {
            "status": "success",
            "negative_doc_count": negative_count,
            "topics": results,
        }

    except Exception as e:
        print(f"[Topics] Error during BERTopic modeling: {e}. Falling back to TF-IDF + KMeans.")
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            X = vectorizer.fit_transform(texts)
            
            num_clusters = min(5, max(2, negative_count // 10))
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
            kmeans.fit(X)
            
            topic_to_docs = {}
            for idx, label_idx in enumerate(kmeans.labels_):
                topic_to_docs.setdefault(int(label_idx), []).append(negative_docs[idx])
            
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            terms = vectorizer.get_feature_names_out()
            
            results = []
            for i in range(num_clusters):
                keywords = [terms[ind] for ind in order_centroids[i, :6]]
                label = ", ".join(keywords[:3])
                count = sum(1 for label_idx in kmeans.labels_ if label_idx == i)
                results.append({
                    "topic_id": i,
                    "label": label,
                    "keywords": keywords,
                    "document_count": int(count),
                    "documents": topic_to_docs.get(i, []),
                })
                
            print(f"[Topics] Extracted {len(results)} negative topic clusters using TF-IDF Fallback.")
            return {
                "status": "success",
                "negative_doc_count": negative_count,
                "topics": results,
            }
        except Exception as fallback_e:
            print(f"[Topics] Fallback clustering also failed: {fallback_e}")
            return {
                "status": "error",
                "reason": str(e),
                "negative_doc_count": negative_count,
                "topics": [],
            }