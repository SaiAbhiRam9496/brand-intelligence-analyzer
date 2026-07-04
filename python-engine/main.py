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


# ── Tab Renderers ────────────────────────────────────────────
def render_overview_tab(data: dict):
    import plotly.graph_objects as go

    sentiment = data["sentiment_summary"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Documents", sentiment["total_docs"])
    col2.metric("Positive", f"{sentiment['positive_pct']}%")
    col3.metric("Negative", f"{sentiment['negative_pct']}%")
    col4.metric("Neutral", f"{sentiment['neutral_pct']}%")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Sentiment Breakdown")
        fig = go.Figure(data=[go.Pie(
            labels=["Positive", "Negative", "Neutral"],
            values=[sentiment["positive_pct"], sentiment["negative_pct"], sentiment["neutral_pct"]],
            hole=0.5,
            marker_colors=["#2ecc71", "#e74c3c", "#95a5a6"],
        )])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Sentiment by Source")
        by_source = sentiment.get("by_source", {})
        sources = list(by_source.keys())
        fig2 = go.Figure(data=[
            go.Bar(name="Positive", x=sources, y=[by_source[s]["Positive"] for s in sources], marker_color="#2ecc71"),
            go.Bar(name="Negative", x=sources, y=[by_source[s]["Negative"] for s in sources], marker_color="#e74c3c"),
            go.Bar(name="Neutral", x=sources, y=[by_source[s]["Neutral"] for s in sources], marker_color="#95a5a6"),
        ])
        fig2.update_layout(barmode="group", margin=dict(t=20, b=20, l=20, r=20), height=350)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top Keywords")
    keywords = data.get("keywords", [])
    if keywords:
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            freq_dict = {kw["keyword"]: kw["score"] for kw in keywords}
            wc = WordCloud(width=900, height=350, background_color="white", colormap="viridis").generate_from_frequencies(freq_dict)

            fig3, ax = plt.subplots(figsize=(10, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig3)
        except Exception:
            st.write(", ".join(kw["keyword"] for kw in keywords))
    else:
        st.info("No keywords extracted.")


def render_negative_tab(data: dict):
    topics_result = data["topics_result"]

    st.subheader("Negative Topic Clusters")
    if topics_result.get("status") == "success":
        for topic in topics_result["topics"]:
            st.markdown(f"**{topic['label']}** — {topic['document_count']} documents")
    else:
        reason = topics_result.get("reason", "Insufficient negative documents for topic modeling.")
        st.warning(f"⚠️ Topic modeling skipped: {reason}")

    st.subheader("Most Negative Content")
    worst_docs = data.get("worst_docs", [])
    if worst_docs:
        df = pd.DataFrame([
            {
                "Source": d.get("source", "").title(),
                "Date": d.get("date", ""),
                "Text": d.get("text", "")[:150],
                "Confidence": d.get("sentiment_confidence", 0),
            }
            for d in worst_docs[:20]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No negative content found.")


def render_strategy_tab(data: dict):
    strategy = data.get("strategy_report", {})
    tone = data.get("tone_result", {})

    if "error" in strategy:
        st.error(f"Strategy generation failed: {strategy['error']}")
        return

    st.subheader("Brand Tone Profile")
    all_scores = tone.get("all_scores", [])
    if all_scores:
        import plotly.graph_objects as go
        fig = go.Figure(data=go.Scatterpolar(
            r=[s["score"] for s in all_scores],
            theta=[s["tone"] for s in all_scores],
            fill="toself",
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Strategy Analysis")
    st.write(strategy.get("current_strategy", "Not available."))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths**")
        for s in strategy.get("strengths", []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("**Weaknesses**")
        for w in strategy.get("weaknesses", []):
            st.markdown(f"- {w}")

    st.subheader("Recommendations")
    for i, rec in enumerate(strategy.get("recommendations", []), 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {rec.get('title', '')}**")
            st.write(rec.get("explanation", ""))


def render_raw_data_tab(data: dict):
    documents = data.get("documents", [])
    if not documents:
        st.info("No documents to display.")
        return

    df = pd.DataFrame([
        {
            "Source": d.get("source", ""),
            "Sentiment": d.get("sentiment", ""),
            "Date": d.get("date", ""),
            "Text": d.get("text", "")[:200],
        }
        for d in documents
    ])

    col1, col2 = st.columns(2)
    with col1:
        source_filter = st.multiselect("Filter by source", options=df["Source"].unique().tolist())
    with col2:
        sentiment_filter = st.multiselect("Filter by sentiment", options=df["Sentiment"].unique().tolist())

    filtered_df = df.copy()
    if source_filter:
        filtered_df = filtered_df[filtered_df["Source"].isin(source_filter)]
    if sentiment_filter:
        filtered_df = filtered_df[filtered_df["Sentiment"].isin(sentiment_filter)]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered_df)} of {len(df)} documents")


def render_pdf_download(data: dict):
    st.subheader("📄 Export Report")

    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF..."):
            output_path = f"report_{data['brand'].replace(' ', '_')}.pdf"
            generate_pdf_report(
                brand=data["brand"],
                output_path=output_path,
                sentiment_summary=data["sentiment_summary"],
                strategy_report=data["strategy_report"],
                tone_result=data["tone_result"],
                topics_result=data["topics_result"],
                worst_docs=data["worst_docs"],
            )

            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=f,
                    file_name=f"{data['brand']}_brand_intelligence_report.pdf",
                    mime="application/pdf",
                )

            os.remove(output_path)


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

        data = st.session_state.analysis_data

        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overview", "🔍 Negative Deep Dive", "🎯 Strategy Report", "📋 Raw Data"
        ])

        # ── Tab 1: Overview ──────────────────────────────────
        with tab1:
            render_overview_tab(data)

        # ── Tab 2: Negative Deep Dive ─────────────────────────
        with tab2:
            render_negative_tab(data)

        # ── Tab 3: Strategy Report ────────────────────────────
        with tab3:
            render_strategy_tab(data)

        # ── Tab 4: Raw Data Explorer ──────────────────────────
        with tab4:
            render_raw_data_tab(data)

        # ── PDF Download ──────────────────────────────────────
        st.divider()
        render_pdf_download(data)


if __name__ == "__main__":
    main()