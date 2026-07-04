# ============================================================
# nlp/relevance_filter.py
# Calculates a relevance score/density of a document to the brand
# Applied to keyword and topic modeling to reduce noise
# ============================================================

import re


def calculate_relevance_score(text: str, title: str, brand: str) -> float:
    """
    Calculates a relevance score for a document.
    Higher weight is given to matches in the title.
    """
    if not brand:
        return 1.0

    brand_lower = brand.lower().strip()
    title_lower = title.lower()
    text_lower = text.lower()

    # Find occurrences (using word boundary check to avoid partial word match)
    pattern = r'\b' + re.escape(brand_lower) + r'\b'
    title_matches = len(re.findall(pattern, title_lower))
    text_matches = len(re.findall(pattern, text_lower))

    total_words = len(text_lower.split()) + len(title_lower.split())
    if total_words == 0:
        return 0.0

    # Weight title matches higher than body matches
    score = (title_matches * 3.0) + text_matches
    
    # Calculate density (matches per 100 words)
    density = (score / total_words) * 100.0
    return round(density, 4)


def add_relevance_scores(documents: list[dict], brand: str) -> list[dict]:
    """
    Computes and adds a relevance score to all documents.
    """
    for doc in documents:
        text = doc.get("text", "")
        title = doc.get("title", "")
        doc["relevance_score"] = calculate_relevance_score(text, title, brand)
    return documents


def filter_relevant_documents(documents: list[dict], brand: str, min_score: float = 0.5) -> list[dict]:
    """
    Filters documents keeping only those that pass a minimum relevance threshold.
    """
    scored_docs = add_relevance_scores(documents, brand)
    filtered = [doc for doc in scored_docs if doc.get("relevance_score", 0.0) >= min_score]
    print(f"[RelevanceFilter] Kept {len(filtered)}/{len(documents)} documents with relevance score >= {min_score}")
    return filtered