"""SERP Analyzer — Fetches Google SERP data via SerperAPI for competitive intelligence."""
import os
import re
import requests
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv(override=True)

logger = get_logger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"


def get_serp_data(keyword, api_key=None, country="br", language="pt-br", num_results=10):
    """Fetch Google SERP data for a keyword via SerperAPI.

    Args:
        keyword: Search query.
        api_key: SerperAPI key (falls back to SERPER_API_KEY env var).
        country: Country code for localized results.
        language: Language code.
        num_results: Number of results to fetch.

    Returns:
        dict with keys: organic, people_also_ask, related_searches, or None on failure.
    """
    key = api_key or os.getenv("SERPER_API_KEY", "")
    if not key:
        logger.warning("SERPER_API_KEY not configured. Skipping SERP analysis.")
        return None

    headers = {
        "X-API-KEY": key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": keyword,
        "gl": country,
        "hl": language,
        "num": num_results,
    }

    try:
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code != 200:
            logger.warning("SerperAPI error (status=%d): %s", response.status_code, response.text[:200])
            return None

        data = response.json()
        return _parse_serp_response(data)

    except requests.RequestException as e:
        logger.warning("SerperAPI request failed: %s", e)
        return None


def _parse_serp_response(data):
    """Parse SerperAPI response into structured SERP brief.

    Returns:
        dict with organic results, PAA questions, related searches.
    """
    organic = []
    for item in data.get("organic", []):
        organic.append({
            "position": item.get("position", 0),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "estimated_word_count": _estimate_word_count(item.get("snippet", "")),
        })

    people_also_ask = []
    for item in data.get("peopleAlsoAsk", []):
        people_also_ask.append({
            "question": item.get("question", ""),
            "snippet": item.get("snippet", ""),
        })

    related_searches = []
    for item in data.get("relatedSearches", []):
        related_searches.append(item.get("query", ""))

    return {
        "organic": organic,
        "people_also_ask": people_also_ask,
        "related_searches": related_searches,
        "total_results": len(organic),
    }


def _estimate_word_count(snippet):
    """Estimate article word count from snippet length.

    Rough heuristic: snippet is ~2% of total article content.
    Average snippet is 150-300 chars (~25-50 words).
    """
    if not snippet:
        return 1500  # default estimate
    snippet_words = len(snippet.split())
    # Rough multiplier: snippet represents ~2-3% of article
    estimated = snippet_words * 40
    return max(800, min(5000, estimated))


def generate_serp_brief(keyword, api_key=None):
    """Generate a complete SERP brief for a keyword.

    This is the main entry point for the pipeline.

    Returns:
        dict with full SERP analysis, or empty dict on failure.
    """
    serp_data = get_serp_data(keyword, api_key=api_key)
    if not serp_data:
        return {}

    # Calculate averages
    word_counts = [r["estimated_word_count"] for r in serp_data["organic"]]
    avg_word_count = int(sum(word_counts) / len(word_counts)) if word_counts else 1800

    # Extract common patterns from top results
    titles = [r["title"] for r in serp_data["organic"]]

    brief = {
        "keyword": keyword,
        "top_results": serp_data["organic"][:10],
        "people_also_ask": serp_data["people_also_ask"],
        "related_searches": serp_data["related_searches"],
        "avg_word_count": avg_word_count,
        "recommended_word_count": int(avg_word_count * 1.2),  # 20% more than average
        "competitor_titles": titles[:5],
    }

    logger.info("SERP brief generated: %d results, %d PAA, %d related, avg %d words",
                len(serp_data["organic"]),
                len(serp_data["people_also_ask"]),
                len(serp_data["related_searches"]),
                avg_word_count)

    return brief
