# ============================================================
# collector/youtube_collector.py
# Fetches YouTube video titles + descriptions for a brand
# Uses YouTube Data API v3 — no comments, no video content
# Returns a list of standardized document dicts
# ============================================================

import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# ── Constants ───────────────────────────────────────────────
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

QUERIES = [
    "{brand}",
    "{brand} review",
    "{brand} campaign",
    "{brand} controversy",
    "{brand} customer experience",
    "{brand} vs",
]

MAX_RESULTS_PER_QUERY = 10  # 6 queries × 10 = 60 videos, well within free quota


# ── Main Collection Function ─────────────────────────────────
def collect_youtube(brand: str) -> list[dict]:
    """
    Fires 6 natural queries against YouTube Data API v3 for the given brand.
    Collects title + description + engagement metrics.
    Returns a list of standardized document dicts.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env file")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    collected = []
    seen_ids = set()  # Deduplicate by video ID

    for query_template in QUERIES:
        query = query_template.replace("{brand}", brand)

        try:
            # Step 1 — Search for videos
            search_response = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=MAX_RESULTS_PER_QUERY,
                relevanceLanguage="en",
                order="relevance",
            ).execute()

            video_items = search_response.get("items", [])

            # Step 2 — Get video IDs for stats lookup
            video_ids = []
            for item in video_items:
                vid_id = item["id"].get("videoId")
                if vid_id and vid_id not in seen_ids:
                    video_ids.append(vid_id)
                    seen_ids.add(vid_id)

            if not video_ids:
                continue

            # Step 3 — Fetch view + like counts in one batch call
            stats_response = youtube.videos().list(
                part="statistics",
                id=",".join(video_ids),
            ).execute()

            stats_map = {}
            for item in stats_response.get("items", []):
                stats_map[item["id"]] = item.get("statistics", {})

            # Step 4 — Build document dicts
            for item in video_items:
                vid_id = item["id"].get("videoId")
                if not vid_id:
                    continue

                snippet = item.get("snippet", {})
                title = snippet.get("title") or ""
                description = snippet.get("description") or ""
                text = f"{title}. {description}".strip()

                # Skip very short content
                if len(text) < 20:
                    continue

                

                stats = stats_map.get(vid_id, {})

                collected.append({
                    "source": "youtube",
                    "text": text,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "date": snippet.get("publishedAt", "")[:10],  # YYYY-MM-DD
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "query_used": query,
                })

        except Exception as e:
            print(f"[YouTubeCollector] Error on query '{query}': {e}")
            continue

    print(f"[YouTubeCollector] Collected {len(collected)} videos for '{brand}'")
    return collected


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    results = collect_youtube("Nike")
    for r in results[:3]:
        print(r)
    print(f"\nTotal: {len(results)} documents")