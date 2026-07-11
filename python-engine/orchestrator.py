# ============================================================
# orchestrator.py
# Coordinates the full NLP and strategy pipeline
# ============================================================

import os
from datetime import datetime

from collector.news_collector import collect_news
from collector.youtube_comments_collector import collect_youtube_comments
from collector.youtube_tone_collector import collect_official_tone_data
from collector.playstore_collector import collect_playstore_reviews
from collector.reddit_collector import collect_reddit_mentions
from collector.wikipedia_collector import collect_wikipedia_context

from nlp.language_filter import filter_english_documents
from nlp.sentiment import analyze_documents
from nlp.keywords import extract_keywords
from nlp.topics import model_negative_topics
from nlp.tone import detect_tone
from nlp.relevance_filter import filter_relevant_documents

from strategy.groq_analysis import generate_strategy_report


def run_full_analysis(brand: str) -> dict:
    """
    Executes the entire multi-source scraping, sentiment, tone,
    and strategic AI recommendation pipeline.
    """
    print(f"[Orchestrator] Starting analysis for brand: '{brand}'")
    pipeline_warnings = []

    # Step 1: Data Collection
    news_docs = []
    try:
        news_docs = collect_news(brand)
    except Exception as e:
        print(f"[Orchestrator] News collection failed: {e}")
        pipeline_warnings.append("NewsAPI data unavailable (Rate Limit or Missing Key).")

    yt_comments = []
    try:
        yt_comments = collect_youtube_comments(brand)
    except Exception as e:
        print(f"[Orchestrator] YouTube comments collection failed: {e}")
        pipeline_warnings.append("YouTube data unavailable (Rate Limit or Quota Exceeded).")

    playstore_docs = []
    try:
        playstore_docs = collect_playstore_reviews(brand)
    except Exception as e:
        print(f"[Orchestrator] Play Store collection failed: {e}")
        pipeline_warnings.append("Play Store data unavailable (App ID not found or Blocked).")

    reddit_docs = []
    try:
        reddit_docs = collect_reddit_mentions(brand)
    except Exception as e:
        print(f"[Orchestrator] Reddit collection failed: {e}")
        pipeline_warnings.append("Reddit data unavailable (Platform 403 Rate Limit / Block).")

    # Combine sentiment pool
    all_docs = news_docs + yt_comments + playstore_docs + reddit_docs

    # Step 2: Language Filtering (drop non-English content)
    all_docs = filter_english_documents(all_docs)

    if not all_docs:
        print("[Orchestrator] No English documents collected. Aborting pipeline.")
        return {
            "brand": brand,
            "error": "No English documents could be collected for this brand name."
        }

    # Step 3: Sentiment Analysis
    analyzed_docs = analyze_documents(all_docs)

    # Step 4: Tone Detection (official YouTube channel content)
    tone_text = ""
    try:
        tone_text = collect_official_tone_data(brand)
    except Exception as e:
        print(f"[Orchestrator] YouTube tone collection failed: {e}")
        pipeline_warnings.append("Official Brand YouTube Tone unavailable.")

    if tone_text:
        tone_result = detect_tone(tone_text)
    else:
        tone_result = {"primary_tone": "Unknown", "all_scores": []}

    # Step 5: Wikipedia Context (supplementary background context for Groq)
    wiki_data = {"source": "wikipedia", "brand": brand, "text": "", "general_text": ""}
    try:
        wiki_data = collect_wikipedia_context(brand)
    except Exception as e:
        print(f"[Orchestrator] Wikipedia context collection failed: {e}")
        pipeline_warnings.append("Wikipedia context unavailable.")

    # Step 6: Filter relevant documents for keywords & topic modeling
    relevant_docs = filter_relevant_documents(analyzed_docs, brand, min_score=0.5)

    # Step 7: Keyword Extraction
    # We pass relevant docs directly (setting brand="" to avoid redundant filtering)
    keywords = extract_keywords(relevant_docs, top_n=25, brand="")

    # Step 8: Dynamic Topic Modeling (negative-sentiment documents only)
    topics_result = model_negative_topics(relevant_docs)

    # Step 9: Build Sentiment Summary
    total = len(analyzed_docs)
    positive = sum(1 for d in analyzed_docs if d["sentiment"] == "Positive")
    negative = sum(1 for d in analyzed_docs if d["sentiment"] == "Negative")
    neutral = sum(1 for d in analyzed_docs if d["sentiment"] == "Neutral")

    by_source = {}
    for source in ["news", "youtube_comment", "playstore", "reddit"]:
        source_docs = [d for d in analyzed_docs if d.get("source") == source]
        by_source[source] = {
            "Positive": sum(1 for d in source_docs if d["sentiment"] == "Positive"),
            "Negative": sum(1 for d in source_docs if d["sentiment"] == "Negative"),
            "Neutral": sum(1 for d in source_docs if d["sentiment"] == "Neutral"),
        }

    sentiment_summary = {
        "total_docs": total,
        "positive_pct": round(positive / total * 100, 1) if total else 0,
        "negative_pct": round(negative / total * 100, 1) if total else 0,
        "neutral_pct": round(neutral / total * 100, 1) if total else 0,
        "by_source": by_source,
    }

    # Step 10: Strategy Recommendations (Groq Llama 3)
    issues = []
    if topics_result.get("status") == "success":
        for i, t in enumerate(topics_result["topics"]):
            issues.append({
                "cluster_label": f"Issue {i+1}",
                "documents": t.get("documents", [])[:5]
            })
    else:
        worst_relevant = sorted(
            [d for d in relevant_docs if d["sentiment"] == "Negative"],
            key=lambda d: d.get("sentiment_confidence", 0),
            reverse=True,
        )[:10]
        for doc in worst_relevant:
            issues.append({
                "cluster_label": None,
                "documents": [doc]
            })

    strategy_report = generate_strategy_report(
        brand=brand,
        sentiment_summary=sentiment_summary,
        keywords=keywords,
        tone_result=tone_result,
        issues=issues,
        wikipedia_context=wiki_data.get("general_text", "")
    )

    # Sort docs by negativity for dashboard tables
    worst_docs = sorted(
        [d for d in analyzed_docs if d["sentiment"] == "Negative"],
        key=lambda d: d.get("sentiment_confidence", 0),
        reverse=True,
    )

    print(f"[Orchestrator] Completed pipeline successfully for '{brand}'")
    return {
        "brand": brand,
        "documents": analyzed_docs,
        "sentiment_summary": sentiment_summary,
        "keywords": keywords,
        "topics_result": topics_result,
        "tone_result": tone_result,
        "strategy_report": strategy_report,
        "wiki_data": wiki_data,
        "worst_docs": worst_docs,
        "issues": issues,
        "pipeline_warnings": pipeline_warnings,
    }


if __name__ == "__main__":
    # Test pipeline execution
    import json
    res = run_full_analysis("Nike")
    print(json.dumps(res, indent=2))
