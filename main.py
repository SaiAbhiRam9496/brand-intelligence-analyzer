# ============================================================
# main.py
# Streamlit app entry point - Brand Intelligence Analyzer
# Orchestrates: Collection -> NLP -> Strategy -> Display/Export
# ============================================================

import streamlit as st
import pandas as pd
import os

from collector.news_collector import collect_news
from collector.youtube_collector import collect_youtube
from collector.web_scraper import collect_website
from nlp.sentiment import analyze_documents
from nlp.keywords import extract_keywords
from nlp.topics import model_negative_topics
from nlp.tone import detect_tone
from strategy.groq_analysis import generate_strategy_report
from report.pdf_generator import generate_pdf_report

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Brand Intelligence Analyzer",
    page_icon="📊",
    layout="wide",
)

# ── Session State Init ──────────────────────────────────────
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = {}


# ── Core Pipeline Function ──────────────────────────────────
@st.cache_data(show_spinner=False)
def run_full_analysis(brand: str) -> dict:
    """
    Runs the complete analysis pipeline for a brand.
    Cached so re-running the UI doesn't re-trigger API calls.
    """
    # Step 1 — Collect data
    news_docs = collect_news(brand)
    youtube_docs = collect_youtube(brand)
    wiki_data = collect_website(brand)

    all_docs = news_docs + youtube_docs

    # Step 2 — Sentiment analysis
    analyzed_docs = analyze_documents(all_docs)

    # Step 3 — Keyword extraction (uses relevance filtering internally)
    keywords = extract_keywords(all_docs, top_n=25, brand=brand)

    # Step 4 — Topic modeling (negative documents only)
    topics_result = model_negative_topics(analyzed_docs)

    # Step 5 — Tone detection (on Wikipedia general text)
    tone_text = wiki_data.get("general_text", "") or wiki_data.get("text", "")
    tone_result = detect_tone(tone_text) if tone_text else {"primary_tone": "Unknown", "all_scores": []}

    # Step 6 — Build sentiment summary
    total = len(analyzed_docs)
    positive = sum(1 for d in analyzed_docs if d["sentiment"] == "Positive")
    negative = sum(1 for d in analyzed_docs if d["sentiment"] == "Negative")
    neutral = sum(1 for d in analyzed_docs if d["sentiment"] == "Neutral")

    by_source = {}
    for source in ["news", "youtube"]:
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

    # Step 7 — Strategy generation (Groq)
    negative_samples = [d["text"] for d in analyzed_docs if d["sentiment"] == "Negative"][:10]
    positive_samples = [d["text"] for d in analyzed_docs if d["sentiment"] == "Positive"][:10]

    strategy_report = generate_strategy_report(
        brand=brand,
        sentiment_summary=sentiment_summary,
        keywords=keywords,
        tone_result=tone_result,
        topics_result=topics_result,
        wikipedia_context=wiki_data.get("general_text", ""),
        sample_negative_docs=negative_samples,
        sample_positive_docs=positive_samples,
    )

    # Sort docs by negativity for "worst content" table
    worst_docs = sorted(
        [d for d in analyzed_docs if d["sentiment"] == "Negative"],
        key=lambda d: d.get("sentiment_confidence", 0),
        reverse=True,
    )

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
    }


# ── Screen 1: Input ──────────────────────────────────────────
def render_input_screen():
    st.title("📊 Brand Intelligence Analyzer")
    st.markdown(
        "Get a deep marketing analysis of any major brand — sentiment, "
        "keywords, brand tone, and AI-generated strategy insights."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        brand_input = st.text_input(
            "Enter a brand name",
            placeholder="e.g. Nike, Apple, Coca-Cola, Samsung...",
        )
    with col2:
        st.write("")
        st.write("")
        analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

    st.caption(
        "⚠️ Works best for large, well-known brands with substantial English-language "
        "online coverage. Niche or small brands may yield limited data."
    )

    if analyze_clicked and brand_input.strip():
        brand = brand_input.strip()

        progress_bar = st.progress(0, text="Starting analysis...")

        progress_bar.progress(10, text="Collecting news...")
        progress_bar.progress(30, text="Fetching YouTube data...")
        progress_bar.progress(50, text="Scanning Wikipedia...")
        progress_bar.progress(65, text="Running sentiment analysis...")
        progress_bar.progress(80, text="Extracting keywords and tone...")
        progress_bar.progress(95, text="Generating strategy report...")

        result = run_full_analysis(brand)

        progress_bar.progress(100, text="Done!")

        st.session_state.analysis_data = result
        st.session_state.analysis_complete = True
        st.rerun()

    elif analyze_clicked:
        st.warning("Please enter a brand name.")


# ── Main App Router ──────────────────────────────────────────
def main():
    if not st.session_state.analysis_complete:
        render_input_screen()
    else:
        st.title(f"📊 Analysis: {st.session_state.analysis_data['brand']}")
        if st.button("← Analyze a different brand"):
            st.session_state.analysis_complete = False
            st.session_state.analysis_data = {}
            st.cache_data.clear()
            st.rerun()

        st.info("Dashboard screens coming next — this confirms the pipeline runs end to end.")
        st.json(st.session_state.analysis_data["sentiment_summary"])


if __name__ == "__main__":
    main()