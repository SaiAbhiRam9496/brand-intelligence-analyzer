# ============================================================
# collector/wikipedia_collector.py
# Pulls brand background context from Wikipedia using the clean Extract API
# Used purely as supplementary context for Groq strategy recommendations
# ============================================================

import requests

HEADERS = {
    "User-Agent": "BrandIntelligenceAnalyzer/1.0 (student portfolio project)"
}

WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
MAX_WORDS = 3000

NEGATIVE_SECTION_KEYWORDS = [
    "criticism", "controversy", "controversies", "lawsuit",
    "scandal", "legal issues", "boycott", "backlash", "allegations"
]


def _is_disambiguation_page(extract: str) -> bool:
    lowered = extract[:300].lower()
    return "may refer to" in lowered or "may also refer to" in lowered


def _find_wikipedia_title(brand: str) -> str | None:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": brand,
        "format": "json",
        "srlimit": 8,
    }

    try:
        response = requests.get(WIKI_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])

        if not results:
            return None

        brand_lower = brand.lower().strip()
        brand_indicators = ["inc", "company", "corporation", "brand", "se", "ltd", "group"]
        candidates = []

        candidates += [r["title"] for r in results if r["title"].lower().strip() == brand_lower]
        candidates += [
            r["title"] for r in results
            if brand_lower in r["title"].lower()
            and any(ind in r["title"].lower() for ind in brand_indicators)
            and r["title"] not in candidates
        ]
        candidates += [
            r["title"] for r in results
            if r["title"].lower().startswith(brand_lower + ",") and r["title"] not in candidates
        ]
        candidates += [r["title"] for r in results if r["title"] not in candidates]

        for title in candidates:
            extract = _get_wikipedia_extract(title)
            if not extract:
                continue
            if _is_disambiguation_page(extract):
                continue
            if len(extract.split()) < 100:
                continue
            return title

        return results[0]["title"] if results else None

    except Exception as e:
        print(f"[WikipediaCollector] Search failed for '{brand}': {e}")
        return None


def _get_wikipedia_extract(title: str) -> str:
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
        print(f"[WikipediaCollector] Failed to fetch extract for '{title}': {e}")
        return ""


def _split_sections(extract: str) -> dict:
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


def collect_wikipedia_context(brand: str) -> dict:
    """
    Main background context collector function.
    """
    print(f"[WikipediaCollector] Fetching context for '{brand}'")
    title = _find_wikipedia_title(brand)

    if not title:
        return {
            "source": "wikipedia", "brand": brand, "text": "",
            "general_text": "", "negative_text": "", "word_count": 0, "title": "",
        }

    extract = _get_wikipedia_extract(title)
    if not extract:
        return {
            "source": "wikipedia", "brand": brand, "text": "",
            "general_text": "", "negative_text": "", "word_count": 0, "title": title,
        }

    sections = _split_sections(extract)
    general_words = sections["general_text"].split()
    if len(general_words) > MAX_WORDS:
        sections["general_text"] = " ".join(general_words[:MAX_WORDS])

    combined_text = sections["general_text"] + " " + sections["negative_text"]
    word_count = len(combined_text.split())

    return {
        "source": "wikipedia",
        "brand": brand,
        "text": combined_text.strip(),
        "general_text": sections["general_text"],
        "negative_text": sections["negative_text"],
        "word_count": word_count,
        "title": title,
    }
