# ============================================================
# nlp/relevance_filter.py
# Filters documents for brand relevance — used selectively by
# tasks that are sensitive to noise (keyword extraction, topic
# modeling), while sentiment analysis uses the full unfiltered
# document set since volume matters more there than precision.
# ============================================================


def filter_relevant_documents(documents: list[dict], brand: str) -> list[dict]:
    """
    Returns only documents where the brand name appears in the title.
    This drops loosely-matched content (brand mentioned in passing,
    false-positive name matches, unrelated articles/videos).

    Args:
        documents: list of document dicts, each with a "title" field
        brand: brand name to check for

    Returns:
        Filtered list of documents
    """
    brand_lower = brand.lower()
    filtered = [
        doc for doc in documents
        if brand_lower in doc.get("title", "").lower()
    ]

    print(f"[RelevanceFilter] {len(filtered)}/{len(documents)} documents kept "
          f"(brand name found in title)")

    return filtered


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_docs = [
        {"title": "Nike Zegamadome x sacai Shoe"},
        {"title": "Tech workers from Amazon, Google, Nike share advice"},
        {"title": "Tere Nike Nike full song Panjabi"},
        {"title": "Apple Card Sign-Up Earn Free AirPods"},
    ]

    result = filter_relevant_documents(test_docs, "Nike")
    for doc in result:
        print(doc["title"])