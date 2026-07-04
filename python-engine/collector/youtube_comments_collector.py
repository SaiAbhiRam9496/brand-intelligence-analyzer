# ============================================================
# collector/youtube_comments_collector.py
# Fetches comment threads from top YouTube search results for a brand
# Returns a list of standardized document dicts
# ============================================================

import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

QUERIES = [
    "{brand} review",
    "{brand} controversy",
    "{brand} customer experience",
]

MAX_VIDEOS_PER_QUERY = 3
MAX_COMMENTS_PER_VIDEO = 15


def collect_youtube_comments(brand: str) -> list[dict]:
    """
    Finds top videos matching brand search queries, then fetches the top comment threads
    for each video. Standardizes outputs to match the collector document structure.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env file")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    collected = []
    seen_comment_ids = set()
    video_ids = set()

    # Step 1: Find target videos
    for query_template in QUERIES:
        query = query_template.replace("{brand}", brand)
        try:
            search_response = youtube.search().list(
                q=query,
                part="id",
                type="video",
                maxResults=MAX_VIDEOS_PER_QUERY,
                relevanceLanguage="en",
                order="relevance",
            ).execute()

            for item in search_response.get("items", []):
                vid_id = item["id"].get("videoId")
                if vid_id:
                    video_ids.add(vid_id)
        except Exception as e:
            print(f"[YouTubeComments] Search error for query '{query}': {e}")

    print(f"[YouTubeComments] Found {len(video_ids)} videos to fetch comments from.")

    # Step 2: Fetch comments for each video
    for vid_id in video_ids:
        try:
            comments_response = youtube.commentThreads().list(
                part="snippet",
                videoId=vid_id,
                maxResults=MAX_COMMENTS_PER_VIDEO,
                textFormat="plainText"
            ).execute()

            for item in comments_response.get("items", []):
                comment_id = item.get("id")
                if comment_id in seen_comment_ids:
                    continue
                seen_comment_ids.add(comment_id)

                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                text = snippet.get("textDisplay", "").strip()

                if len(text) < 10:
                    continue

                date = snippet.get("publishedAt", "")[:10]  # YYYY-MM-DD
                likes = int(snippet.get("likeCount", 0))

                collected.append({
                    "source": "youtube_comment",
                    "text": text,
                    "date": date,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "raw_metadata": {
                        "comment_id": comment_id,
                        "likes": likes,
                        "author": snippet.get("authorDisplayName", "")
                    }
                })
        except Exception as e:
            # Some videos might have comments disabled
            print(f"[YouTubeComments] Could not fetch comments for video {vid_id}: {e}")
            continue

    print(f"[YouTubeComments] Collected {len(collected)} comments for '{brand}'")
    return collected


if __name__ == "__main__":
    # Standalone quick test
    results = collect_youtube_comments("Nike")
    for r in results[:3]:
        print(r)
    print(f"\nTotal collected comments: {len(results)}")
