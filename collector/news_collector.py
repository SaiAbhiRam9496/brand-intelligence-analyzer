# ============================================================
# collector/news_collector.py
# Fetches news headlines + descriptions for a brand using NewsAPI
# Returns a list of standardized document dicts
# ============================================================

import os
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

# ── Constants ───────────────────────────────────────────────
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

QUERIES = [
    "{brand}",
    "{brand} review",
    "{brand} campaign",
    "{brand} controversy",
    "{brand} customer experience",
    "{brand} vs",
]

MAX_RESULTS_PER_QUERY = 20  # Free tier: 100/day total, 20 per query × 6 queries = 120


# ── Main Collection Function ─────────────────────────────────
def collect_news(brand: str) -> list[dict]:
    """
    Fires 6 natural queries against NewsAPI for the given brand.
    Returns a list of document dicts with standardized fields.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not found in .env file")

    client = NewsApiClient(api_key=NEWS_API_KEY)

    # NewsAPI free tier only allows articles from last 30 days
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    collected = []
    seen_urls = set()  # Deduplicate by URL

    for query_template in QUERIES:
        query = query_template.replace("{brand}", brand)

        try:
            response = client.get_everything(
                q=query,
                from_param=date_from,
                language="en",
                sort_by="relevancy",
                page_size=MAX_RESULTS_PER_QUERY,
            )

            articles = response.get("articles", [])

            for article in articles:
                url = article.get("url", "")

                # Skip duplicates
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Combine title + description as the text content
                title = article.get("title") or ""
                description = article.get("description") or ""
                text = f"{title}. {description}".strip()

                # Skip empty or very short content
                if len(text) < 20:
                    continue

                collected.append({
                    "source": "news",
                    "text": text,
                    "title": title,
                    "url": url,
                    "date": article.get("publishedAt", "")[:10],  # YYYY-MM-DD only
                    "query_used": query,
                })

        except Exception as e:
            print(f"[NewsCollector] Error on query '{query}': {e}")
            continue

    print(f"[NewsCollector] Collected {len(collected)} articles for '{brand}'")
    return collected


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    results = collect_news("Nike")
    for r in results[:3]:
        print(r)
    print(f"\nTotal: {len(results)} documents")