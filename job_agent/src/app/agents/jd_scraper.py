from __future__ import annotations

"""JD Scraper Agent

Collects job descriptions from multiple sources based on the candidate's
target role, city and sector. Supports three strategies:

1. Structured search via a search-engine scrape (no API key needed).
2. Direct fetch of a known company careers page URL.
3. Manual paste fallback — if jd_urls is empty, uses jd_text already in state.

All collected JDs are stored as a list[dict] in state["collected_jds"].
Each entry has keys: title, company, city, source_url, raw_text.
"""

import logging
import time
from typing import Dict, List
from urllib import error, request
from urllib.parse import quote_plus

from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _fetch(url: str, timeout: int = 15) -> str:
    req = request.Request(url, headers=_HEADERS)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except (error.URLError, TimeoutError) as exc:
        logger.warning("_fetch failed for %s: %s", url, exc)
        return ""


def _strip_tags(html: str) -> str:
    """Very lightweight tag stripper — avoids a BeautifulSoup dependency."""
    import re
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _google_search_urls(query: str, max_results: int = 5) -> List[str]:
    """
    Use a DuckDuckGo HTML search to find JD URLs — no API key needed.
    Returns up to `max_results` URLs.
    """
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    html = _fetch(search_url)
    if not html:
        return []
    import re
    # DDG HTML result links look like: <a class="result__a" href="https://...">
    urls = re.findall(r'result__a[^>]*href="(https://[^"]+)"', html)
    # filter out DDG-internal links
    urls = [u for u in urls if "duckduckgo.com" not in u]
    return urls[:max_results]


def _jd_from_url(url: str) -> dict | None:
    html = _fetch(url)
    if not html:
        return None
    text = _strip_tags(html)[:3000]  # first 3 000 chars is usually enough
    if len(text) < 100:
        return None
    return {
        "title": "unknown",
        "company": "unknown",
        "city": "unknown",
        "source_url": url,
        "raw_text": text,
    }


# ---------------------------------------------------------------------------
# public agent
# ---------------------------------------------------------------------------


def jd_scraper_agent(state: InvestmentJobState) -> Dict[str, List[dict]]:
    """
    Collect JDs based on state inputs.

    Reads from state:
        target_city   — e.g. "Hong Kong" or "Shanghai"
        target_sector — e.g. "healthcare", "tmt", "new energy"
        jd_urls       — optional list of explicit URLs to fetch
        jd_text       — fallback: if provided and no URLs, wrap it as one entry

    Writes to state:
        collected_jds — list[dict] with keys title/company/city/source_url/raw_text
    """
    city = state.get("target_city") or "Hong Kong"
    sector = state.get("target_sector") or "equity research"
    explicit_urls: List[str] = state.get("jd_urls") or []
    existing_jd_text: str = state.get("jd_text") or ""

    collected: List[dict] = []

    # ── 1. explicit URLs ─────────────────────────────────────────────────────
    for url in explicit_urls[:10]:
        entry = _jd_from_url(url)
        if entry:
            collected.append(entry)
        time.sleep(0.5)  # polite delay

    # ── 2. search-based discovery (if <3 results so far) ────────────────────
    if len(collected) < 3:
        queries = [
            f"{sector} analyst {city} job site:linkedin.com",
            f"{sector} equity research {city} 招聘",
            f"{sector} research analyst {city} careers",
        ]
        seen_urls: set[str] = {e["source_url"] for e in collected}
        for q in queries:
            if len(collected) >= 8:
                break
            urls = _google_search_urls(q, max_results=3)
            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                entry = _jd_from_url(url)
                if entry:
                    entry["city"] = city
                    collected.append(entry)
                time.sleep(0.5)

    # ── 3. fallback: existing jd_text from state ─────────────────────────────
    if not collected and existing_jd_text:
        collected.append({
            "title": "manual paste",
            "company": "unknown",
            "city": city,
            "source_url": "manual",
            "raw_text": existing_jd_text,
        })

    logger.info("jd_scraper_agent: collected %d JDs.", len(collected))
    return {"collected_jds": collected}
