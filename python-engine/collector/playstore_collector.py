# ============================================================
# collector/playstore_collector.py
# Fetches reviews for a brand's mobile application from Google Play Store
# Returns a list of standardized document dicts
# ============================================================

from google_play_scraper import search, reviews, Sort
from datetime import datetime

MAX_REVIEWS_TO_COLLECT = 50


def _find_app_id(brand: str) -> str | None:
    """
    Searches the Play Store for the brand and attempts to resolve a valid App ID
    by prioritizing apps with non-None appId that match the brand name.
    """
    brand_lower = brand.lower().strip()
    try:
        results = search(brand, lang="en", country="us", n_hits=10)
        if not results:
            return None

        # Priority 1: Match where brand is in the title or appId
        for app in results:
            app_id = app.get("appId")
            if not app_id:
                continue
            title = app.get("title", "").lower()
            app_id_lower = app_id.lower()
            if brand_lower in title or brand_lower in app_id_lower:
                return app_id

        # Priority 2: Fallback to the first non-None appId
        for app in results:
            app_id = app.get("appId")
            if app_id:
                return app_id

    except Exception as e:
        print(f"[PlayStoreCollector] Search error for brand '{brand}': {e}")
    return None


def collect_playstore_reviews(brand: str) -> list[dict]:
    """
    Finds the brand's mobile app on the Play Store, fetches recent reviews,
    and returns standardized document dictionaries.
    """
    app_id = _find_app_id(brand)
    if not app_id:
        print(f"[PlayStoreCollector] No mobile app resolved for brand '{brand}'")
        return []

    print(f"[PlayStoreCollector] Resolved app ID: '{app_id}' for brand '{brand}'")

    collected = []
    try:
        result, _ = reviews(
            app_id,
            lang="en",
            country="us",
            sort=Sort.NEWEST,
            count=MAX_REVIEWS_TO_COLLECT
        )

        for rev in result:
            text = rev.get("content", "").strip()
            # Skip very short/empty reviews
            if len(text) < 10:
                continue

            # Convert date to YYYY-MM-DD format
            date_val = rev.get("at")
            if isinstance(date_val, datetime):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)[:10]

            collected.append({
                "source": "playstore",
                "text": text,
                "date": date_str,
                "url": f"https://play.google.com/store/apps/details?id={app_id}",
                "raw_metadata": {
                    "review_id": rev.get("reviewId"),
                    "userName": rev.get("userName"),
                    "rating": rev.get("score"),
                    "thumbsUpCount": rev.get("thumbsUpCount")
                }
            })

    except Exception as e:
        print(f"[PlayStoreCollector] Error fetching reviews for '{app_id}': {e}")

    print(f"[PlayStoreCollector] Collected {len(collected)} reviews for '{brand}'")
    return collected


if __name__ == "__main__":
    # Standalone quick test
    for test_brand in ["Nike", "Puma"]:
        print(f"\n--- Testing Play Store reviews for {test_brand} ---")
        results = collect_playstore_reviews(test_brand)
        for r in results[:3]:
            print(r)
        print(f"Total collected: {len(results)}")
