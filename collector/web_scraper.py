# ============================================================
# collector/web_scraper.py
# Scrapes brand's own website for tone analysis
# Strategy: BeautifulSoup first → Playwright fallback if JS-rendered
# Scrapes: homepage + /about + /blog (or /news)
# Returns a single combined text block
# ============================================================

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# ── Constants ───────────────────────────────────────────────
MIN_WORDS = 200  # Below this = JS-rendered site, trigger Playwright

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Known content-rich subdomains per brand ──────────────────
BRAND_URLS = {
    "nike": [
        "https://about.nike.com",
        "https://news.nike.com",
    ],
    "coca-cola": [
        "https://www.coca-colacompany.com/about-us",
        "https://www.coca-colacompany.com/news",
    ],
    "apple": [
        "https://www.apple.com/newsroom",
        "https://www.apple.com/leadership",
    ],
    "samsung": [
        "https://news.samsung.com/global",
        "https://www.samsung.com/us/about-samsung",
    ],
}

# Default paths for unknown brands
DEFAULT_PATHS = ["", "/about", "/newsroom", "/press"]


# ── BeautifulSoup Scraper ────────────────────────────────────
def _scrape_with_bs4(url: str) -> str:
    """
    Attempts static HTML scraping with BeautifulSoup.
    Returns extracted text or empty string if it fails.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style, nav, footer noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    except Exception as e:
        print(f"[WebScraper] BS4 failed for {url}: {e}")
        return ""


# ── Playwright Scraper ───────────────────────────────────────
def _scrape_with_playwright(url: str) -> str:
    """
    Opens a real browser with Playwright to handle JS-rendered pages.
    Used as fallback when BeautifulSoup gets insufficient content.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)  # Wait for JS to render

            # Remove noise elements via JS
            page.evaluate("""
                () => {
                    ['script','style','nav','footer','header'].forEach(tag => {
                        document.querySelectorAll(tag).forEach(el => el.remove())
                    })
                }
            """)

            text = page.inner_text("body")
            browser.close()
            return text

    except Exception as e:
        print(f"[WebScraper] Playwright failed for {url}: {e}")
        return ""


# ── Single Page Scraper ──────────────────────────────────────
def _scrape_page(url: str) -> str:
    """
    Tries BS4 first. If content < MIN_WORDS, falls back to Playwright.
    """
    text = _scrape_with_bs4(url)
    word_count = len(text.split())

    if word_count < MIN_WORDS:
        print(f"[WebScraper] BS4 got {word_count} words from {url} — switching to Playwright")
        text = _scrape_with_playwright(url)

    return text


# ── Main Collection Function ─────────────────────────────────
def collect_website(brand: str, base_url: str) -> dict:
    """
    Scrapes brand website for tone analysis.
    Uses known content-rich URLs for major brands,
    falls back to default paths for others.
    """
    brand_key = brand.lower()
    all_text_parts = []

    # Check if we have known good URLs for this brand
    if brand_key in BRAND_URLS:
        urls_to_scrape = BRAND_URLS[brand_key]
        print(f"[WebScraper] Using known content URLs for {brand}")
    else:
        base_url = base_url.rstrip("/")
        urls_to_scrape = [f"{base_url}{path}" for path in DEFAULT_PATHS]

    for url in urls_to_scrape:
        print(f"[WebScraper] Scraping {url}")
        text = _scrape_page(url)
        if text:
            all_text_parts.append(text)

    combined_text = " ".join(all_text_parts)
    word_count = len(combined_text.split())

    print(f"[WebScraper] Total words scraped from {brand} website: {word_count}")

    return {
        "source": "website",
        "brand": brand,
        "text": combined_text,
        "word_count": word_count,
        "base_url": base_url if brand_key not in BRAND_URLS else urls_to_scrape[0],
    }


# ── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    result = collect_website("Nike", "https://www.nike.com")
    print(f"\nWord count: {result['word_count']}")
    print(f"Preview: {result['text'][:300]}")