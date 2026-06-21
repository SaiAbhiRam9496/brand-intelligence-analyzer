# ============================================================
# strategy/groq_analysis.py
# Feeds all analyzed data to Groq (Llama 3) to generate:
# - Brand's current marketing strategy based on evidence
# - Strengths and weaknesses
# - Where competitors are winning
# - 5 specific actionable recommendations
# ============================================================

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Constants ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"  # Current production Llama 3 model on Groq

MAX_KEYWORDS_TO_SEND = 25
MAX_SAMPLE_DOCS = 10  # Sample of negative + positive docs to give Groq concrete examples


def _build_prompt(
    brand: str,
    sentiment_summary: dict,
    keywords: list[dict],
    tone_result: dict,
    topics_result: dict,
    wikipedia_context: str,
    sample_negative_docs: list[str],
    sample_positive_docs: list[str],
) -> str:
    """
    Constructs a structured prompt feeding all analyzed data to Groq.
    """
    keyword_list = ", ".join(kw["keyword"] for kw in keywords[:MAX_KEYWORDS_TO_SEND])

    topics_section = "Not available (insufficient negative document volume for topic modeling)."
    if topics_result.get("status") == "success":
        topic_lines = [
            f"- {t['label']} ({t['document_count']} documents)"
            for t in topics_result["topics"]
        ]
        topics_section = "\n".join(topic_lines)

    negative_examples = "\n".join(f"- {doc[:200]}" for doc in sample_negative_docs[:MAX_SAMPLE_DOCS])
    positive_examples = "\n".join(f"- {doc[:200]}" for doc in sample_positive_docs[:MAX_SAMPLE_DOCS])

    prompt = f"""You are a senior brand strategy consultant analyzing {brand} based on real collected data.

## SENTIMENT OVERVIEW
Positive: {sentiment_summary['positive_pct']}%
Negative: {sentiment_summary['negative_pct']}%
Neutral: {sentiment_summary['neutral_pct']}%
Total documents analyzed: {sentiment_summary['total_docs']}

## TOP KEYWORDS FROM PUBLIC CONVERSATION
{keyword_list}

## BRAND'S OWN TONE (from Wikipedia/brand context)
Primary tone detected: {tone_result.get('primary_tone', 'Unknown')}

## NEGATIVE TOPIC CLUSTERS (root causes of negative sentiment)
{topics_section}

## SAMPLE NEGATIVE CONTENT
{negative_examples if negative_examples else "Limited negative samples available."}

## SAMPLE POSITIVE CONTENT
{positive_examples if positive_examples else "Limited positive samples available."}

## BRAND BACKGROUND CONTEXT (Wikipedia)
{wikipedia_context[:1500]}

---

Based ONLY on the evidence above, provide:

1. **Current Marketing Strategy** (2-3 sentences): What strategy does the evidence suggest {brand} is currently pursuing?

2. **Strengths** (3 bullet points): What is working well, based on the data?

3. **Weaknesses** (3 bullet points): What is working against the brand, based on the data?

4. **5 Specific Actionable Recommendations**: Concrete, specific actions — not generic advice. Each should directly address something visible in the data above.

Be specific and evidence-based. Do not invent facts not supported by the data provided. If data is limited in some area, acknowledge that honestly rather than speculating.

Respond in clean JSON format with this exact structure:
{{
  "current_strategy": "...",
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "recommendations": [
    {{"title": "...", "explanation": "..."}},
    {{"title": "...", "explanation": "..."}},
    {{"title": "...", "explanation": "..."}},
    {{"title": "...", "explanation": "..."}},
    {{"title": "...", "explanation": "..."}}
  ]
}}

Return ONLY the JSON object, no other text before or after."""

    return prompt


# ── Main Function — Generate Strategy Report ───────────────────
def generate_strategy_report(
    brand: str,
    sentiment_summary: dict,
    keywords: list[dict],
    tone_result: dict,
    topics_result: dict,
    wikipedia_context: str,
    sample_negative_docs: list[str],
    sample_positive_docs: list[str],
) -> dict:
    """
    Sends all analyzed brand data to Groq and returns a structured
    strategy report.

    Returns:
        Dict matching the JSON structure requested in the prompt,
        or {"error": "..."} if generation fails.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = _build_prompt(
        brand, sentiment_summary, keywords, tone_result,
        topics_result, wikipedia_context, sample_negative_docs, sample_positive_docs,
    )

    print(f"[GroqStrategy] Generating strategy report for '{brand}'...")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000,
        )

        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        report = json.loads(raw_text)
        print("[GroqStrategy] Strategy report generated successfully.")
        return report

    except json.JSONDecodeError as e:
        print(f"[GroqStrategy] Failed to parse JSON response: {e}")
        return {"error": "Failed to parse strategy report. Please try again."}

    except Exception as e:
        print(f"[GroqStrategy] Error generating strategy report: {e}")
        return {"error": str(e)}


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    test_sentiment = {
        "positive_pct": 52.0,
        "negative_pct": 37.9,
        "neutral_pct": 10.2,
        "total_docs": 177,
    }

    test_keywords = [
        {"keyword": "nike zegama", "score": 0.67},
        {"keyword": "sacai shoe", "score": 0.50},
        {"keyword": "caitlin clark", "score": 0.22},
        {"keyword": "vaporfly shoes", "score": 0.58},
    ]

    test_tone = {"primary_tone": "Inspirational"}

    test_topics = {"status": "skipped", "negative_doc_count": 67}

    test_wiki = (
        "Nike, Inc. is an American athletic footwear and apparel corporation "
        "headquartered near Beaverton, Oregon. It is the world's largest supplier "
        "of athletic shoes and apparel."
    )

    test_negative = [
        "Customers are suing Nike over IEEPA tariff refunds.",
        "Nike faces criticism over labor practices in overseas factories.",
    ]

    test_positive = [
        "Nike releases new sustainable sneaker line, well received by customers.",
        "Nike's collaboration with sacai gets praised by sneaker community.",
    ]

    result = generate_strategy_report(
        "Nike", test_sentiment, test_keywords, test_tone,
        test_topics, test_wiki, test_negative, test_positive,
    )

    print("\n" + json.dumps(result, indent=2))