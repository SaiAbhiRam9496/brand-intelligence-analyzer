# ============================================================
# collector/youtube_tone_collector.py
# Fetches titles + descriptions from official brand channel on YouTube
# Used strictly for brand tone detection, kept separate from sentiment pool
# ============================================================

import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def collect_official_tone_data(brand: str) -> str:
    """
    Finds the official YouTube channel for the brand, then fetches titles and
    descriptions of the top 15 videos from that channel.
    Returns a single combined text block suitable for tone detection.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env file")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    try:
        # Step 1: Search for the channel matching the brand
        channel_search = youtube.search().list(
            q=brand,
            part="snippet",
            type="channel",
            maxResults=1,
        ).execute()

        items = channel_search.get("items", [])
        if not items:
            print(f"[YouTubeTone] No official channel found for brand '{brand}'")
            return ""

        channel_id = items[0]["id"].get("channelId")
        channel_title = items[0]["snippet"].get("title", "")
        print(f"[YouTubeTone] Found channel '{channel_title}' (ID: {channel_id}) for brand '{brand}'")

        # Step 2: Fetch top videos from this channel
        video_search = youtube.search().list(
            channelId=channel_id,
            part="snippet",
            type="video",
            maxResults=15,
            order="relevance",
        ).execute()

        video_items = video_search.get("items", [])
        corpus_parts = []

        for item in video_items:
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            corpus_parts.append(f"{title}. {description}")

        combined_text = "\n".join(corpus_parts).strip()
        print(f"[YouTubeTone] Collected official content: {len(video_items)} videos ({len(combined_text.split())} words)")
        return combined_text

    except Exception as e:
        print(f"[YouTubeTone] Error collecting tone data for '{brand}': {e}")
        return ""


if __name__ == "__main__":
    # Quick standalone test
    text_result = collect_official_tone_data("Nike")
    print(f"\nCollected Word Count: {len(text_result.split())}")
    print("Preview:\n", text_result[:300])
