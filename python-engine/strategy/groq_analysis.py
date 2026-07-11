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
    issues: list[dict],
    wikipedia_context: str,
) -> str:
    """
    Constructs a structured prompt feeding all analyzed data to Groq.
    """
    keyword_list = ", ".join(kw["keyword"] for kw in keywords[:MAX_KEYWORDS_TO_SEND])

    issues_section = ""
    for idx, issue in enumerate(issues):
        label = issue.get("cluster_label") or f"Individual Complaint {idx+1}"
        issues_section += f"\n### ISSUE: {label}\n"
        for doc in issue["documents"]:
            source = doc.get("source", "Unknown")
            date = doc.get("date", "Unknown")
            text = doc.get("text", "")
            issues_section += f"- [Source: {source}, Date: {date}]: {text}\n"

    prompt = f"""You are a senior brand strategy consultant analyzing the brand **{brand}** based on real collected data.

IMPORTANT: The collected data contains noise. You may see mentions of other brands, people, or unrelated products. You MUST ignore those. Your ONLY focus is **{brand}**. Ensure your strategy report explicitly targets **{brand}** and its products/services.

## SENTIMENT OVERVIEW
Positive: {sentiment_summary['positive_pct']}%
Negative: {sentiment_summary['negative_pct']}%
Neutral: {sentiment_summary['neutral_pct']}%
Total documents analyzed: {sentiment_summary['total_docs']}

## TOP KEYWORDS FROM PUBLIC CONVERSATION
{keyword_list}

## BRAND'S OWN TONE (from brand's official YouTube channel content)
Primary tone detected: {tone_result.get('primary_tone', 'Unknown')}

## KEY NEGATIVE ISSUES & EVIDENCE
{issues_section if issues else "No significant negative issues found."}

## BRAND BACKGROUND CONTEXT (Wikipedia)
{wikipedia_context[:1500]}

---

Based ONLY on the evidence above, provide:

1. **Current Marketing Strategy** (2-3 sentences): What strategy does the evidence suggest {brand} is currently pursuing?

2. **Strengths** (3 bullet points): What is working well for {brand}, based on the data?

3. **Weaknesses** (3 bullet points): What is working against {brand}, based on the data?

4. **Issue-Specific Recommendations**: For EACH issue listed above, provide a concrete, specific recommendation that directly addresses the complaint. This MUST be formatted as a 2-3 point bulleted action plan explaining exactly HOW to solve the issue. Use standard dash (-) bullets. Do NOT provide brief one-liners or a single giant paragraph.

Be specific and evidence-based. Do not invent facts not supported by the data provided. If data is limited in some area, acknowledge that honestly rather than speculating.

Respond in clean JSON format with this exact structure:
{{
  "current_strategy": "...",
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "issue_recommendations": [
    {{
      "cluster_label": "...",
      "recommendation": "..."
    }}
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
    issues: list[dict],
    wikipedia_context: str,
) -> dict:
    """
    Sends all analyzed brand data to Groq and returns a structured
    strategy report. Uses JSON mode + retry for reliability.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = _build_prompt(
        brand, sentiment_summary, keywords, tone_result,
        issues, wikipedia_context
    )

    print(f"[GroqStrategy] Generating strategy report for '{brand}'...")

    return _call_groq_with_retry(client, prompt, max_retries=2)


def _call_groq_with_retry(client: Groq, prompt: str, max_retries: int = 2) -> dict:
    """
    Calls Groq with JSON mode enabled and retries on parse failure.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content.strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            report = json.loads(raw_text)
            print(f"[GroqStrategy] Strategy report generated successfully (attempt {attempt}).")
            return report

        except json.JSONDecodeError as e:
            print(f"[GroqStrategy] Attempt {attempt} failed to parse JSON: {e}")

        except Exception as e:
            print(f"[GroqStrategy] Attempt {attempt} error: {e}")
            return {"error": str(e)}

    return {"error": f"Failed to parse strategy report after {max_retries} attempts. Please try again."}

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