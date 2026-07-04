# ============================================================
# collector/reddit_collector.py
# Fetches recent Reddit search results for a brand using public JSON endpoint
# Returns a list of standardized document dicts
# ============================================================

import requests
import time
from datetime import datetime

HEADERS = {
    # Reddit requires a unique and descriptive User-Agent, or it will return a 429
    "User-Agent": "BrandIntelligenceAnalyzer/1.0 (student portfolio project; contact: brandintel@example.org)"
}

MAX_REDDIT_RESULTS = 30


def collect_reddit_mentions(brand: str) -> list[dict]:
    """
    Queries old.reddit.com search endpoint in JSON format for the brand.
    Parses posts, combining title and text content, and returns standard document dicts.
    """
    url = f"https://old.reddit.com/search.json"
    params = {
        "q": brand,
        "sort": "new",
        "limit": MAX_REDDIT_RESULTS
    }

    collected = []
    try:
        print(f"[RedditCollector] Querying Reddit search for '{brand}'")
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)

        # Handle rate limits or standard HTTP errors
        if response.status_code == 429:
            print("[RedditCollector] Rate limited (429) by Reddit. Skipping Reddit collection this run.")
            return []
        response.raise_for_status()

        data = response.json()
        posts = data.get("data", {}).get("children", [])

        for post in posts:
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            
            # Combine title and selftext
            text = f"{title}. {selftext}".strip()
            if len(text) < 15:
                continue

            # Convert created_utc timestamp to YYYY-MM-DD
            created_utc = post_data.get("created_utc")
            if created_utc:
                date_str = datetime.utcfromtimestamp(created_utc).strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")

            permalink = post_data.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else ""

            collected.append({
                "source": "reddit",
                "text": text,
                "date": date_str,
                "url": post_url,
                "raw_metadata": {
                    "subreddit": post_data.get("subreddit"),
                    "score": post_data.get("score"),
                    "num_comments": post_data.get("num_comments"),
                    "author": post_data.get("author")
                }
            })

    except Exception as e:
        print(f"[RedditCollector] Error fetching from Reddit for '{brand}': {e}")

    print(f"[RedditCollector] Collected {len(collected)} posts for '{brand}'")
    return collected


if __name__ == "__main__":
    # Standalone quick test
    results = collect_reddit_mentions("Nike")
    for r in results[:3]:
        print(r)
    print(f"\nTotal collected: {len(results)}")
