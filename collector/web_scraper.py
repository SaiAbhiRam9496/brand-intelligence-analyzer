# ============================================================
# collector/web_scraper.py
# Pulls brand background context from Wikipedia using the
# clean Extract API (plain text, no HTML parsing headaches).
# Used as supplementary context for the Groq strategy report —
# NOT as a sentiment source. Sentiment comes from News + YouTube.
# ============================================================

import requests

# ── Constants ───────────────────────────────────────────────
HEADERS = {
    "User-Agent": "BrandIntelligenceAnalyzer/1.0 (student portfolio project)"
}

WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
MAX_WORDS = 3000  # Cap context length — we don't need the whole article

# Section headers that indicate negative/critical content, if present
NEGATIVE_SECTION_KEYWORDS = [
    "criticism", "controversy", "controversies", "lawsuit",
    "scandal", "legal issues", "boycott", "backlash", "allegations"
]


# ── Step 1: Find the correct Wikipedia page title ────────────
def _find_wikipedia_title(brand: str) -> str | None:
    """
    Searches Wikipedia for the brand. Tries to avoid disambiguation
    pages by preferring results with 'company', 'brand', 'Inc' etc.
    in the title or snippet, falling back to the top result.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": brand,
        "format": "json",
        "srlimit": 5,
    }

    try:
        response = requests.get(WIKI_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])

        if not results:
            return None

        # Prefer a result that looks like a company/brand page
        brand_indicators = ["inc", "company", "corporation", "brand", "se", "ltd", "group"]
        for result in results:
            title_lower = result["title"].lower()
            if any(ind in title_lower for ind in brand_indicators):
                return result["title"]

        # Fallback: just take the top result
        return results[0]["title"]

    except Exception as e:
        print(f"[WebScraper] Wikipedia search failed for '{brand}': {e}")
        return None


# ── Step 2: Get clean plain-text extract ──────────────────────
def _get_wikipedia_extract(title: str) -> str:
    """
    Fetches the clean plain-text extract for a Wikipedia page title
    using the Extract API — no HTML parsing required.
    """
    params = {
        "action": "query",
        "prop": "extracts",
        "titles": title,
        "format": "json",
        "explaintext": True,
    }

    try:
        response = requests.get(WIKI_API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})

        for page_id, page in pages.items():
            return page.get("extract", "")

        return ""

    except Exception as e:
        print(f"[WebScraper] Failed to fetch extract for '{title}': {e}")
        return ""


# ── Step 3: Split into general vs negative sections ───────────
def _split_sections(extract: str) -> dict:
    """
    Parses the '== Heading ==' style sections from the plain-text
    extract and separates any negative/critical sections from
    general content, if they exist.
    """
    general_parts = []
    negative_parts = []
    current_is_negative = False

    for line in extract.split("\n"):
        stripped = line.strip()

        if stripped.startswith("==") and stripped.endswith("=="):
            heading = stripped.strip("=").strip().lower()
            current_is_negative = any(kw in heading for kw in NEGATIVE_SECTION_KEYWORDS)
            continue

        if len(stripped) < 30:
            continue

        if current_is_negative:
            negative_parts.append(stripped)
        else:
            general_parts.append(stripped)

    return {
        "general_text": " ".join(general_parts),
        "negative_text": " ".join(negative_parts),
    }


# ── Main Collection Function ─────────────────────────────────
def collect_website(brand: str, base_url: str = "") -> dict:
    """
    Fetches brand background context from Wikipedia.
    Used as supplementary context for Groq, capped at MAX_WORDS.

    Args:
        brand: Brand name e.g. "Nike"
        base_url: Kept for compatibility, not used

    Returns:
        Dict with general_text, negative_text (if any), combined text, metadata
    """
    print(f"[WebScraper] Searching Wikipedia for '{brand}'")
    title = _find_wikipedia_title(brand)

    if not title:
        print(f"[WebScraper] No Wikipedia page found for '{brand}'")
        return {
            "source": "wikipedia", "brand": brand, "text": "",
            "general_text": "", "negative_text": "", "word_count": 0, "title": "",
        }

    print(f"[WebScraper] Found Wikipedia page: '{title}'")
    extract = _get_wikipedia_extract(title)

    if not extract:
        return {
            "source": "wikipedia", "brand": brand, "text": "",
            "general_text": "", "negative_text": "", "word_count": 0, "title": title,
        }

    sections = _split_sections(extract)

    # Cap general text length — we only need enough for context
    general_words = sections["general_text"].split()
    if len(general_words) > MAX_WORDS:
        sections["general_text"] = " ".join(general_words[:MAX_WORDS])

    combined_text = sections["general_text"] + " " + sections["negative_text"]
    word_count = len(combined_text.split())

    has_negative = len(sections["negative_text"].split()) > 0
    print(f"[WebScraper] Total words: {word_count} "
          f"(general: {len(sections['general_text'].split())}, "
          f"negative/critical section found: {has_negative})")

    return {
        "source": "wikipedia",
        "brand": brand,
        "text": combined_text.strip(),
        "general_text": sections["general_text"],
        "negative_text": sections["negative_text"],
        "word_count": word_count,
        "title": title,
    }


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    for brand in ["Nike", "Puma", "Coca-Cola"]:
        print(f"\n=== Testing: {brand} ===")
        result = collect_website(brand)
        print(f"Title matched: {result['title']}")
        print(f"Word count: {result['word_count']}")
        print(f"Preview: {result['general_text'][:200]}")