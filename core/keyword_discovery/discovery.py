"""Auto Keyword Discovery — Finds new keyword opportunities from multiple sources."""
import re
import requests
from core.agents.serp_analyzer import generate_serp_brief
from core.logger import get_logger

logger = get_logger(__name__)


def google_suggest(keyword, language="pt-BR", country="br"):
    """Fetch Google Autocomplete suggestions for a keyword.

    Uses the public Google Suggest API (no key required).

    Returns:
        List of suggestion strings.
    """
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "q": keyword,
        "hl": language,
        "gl": country,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Response format: ["query", ["suggestion1", "suggestion2", ...]]
            suggestions = data[1] if len(data) > 1 else []
            # Filter out the original query
            suggestions = [s for s in suggestions if s.lower() != keyword.lower()]
            logger.info("Google Suggest: %d suggestions for '%s'", len(suggestions), keyword)
            return suggestions
    except Exception as e:
        logger.warning("Google Suggest failed for '%s': %s", keyword, e)

    return []


def expand_with_modifiers(keyword):
    """Expand a keyword with common search modifiers.

    Returns:
        List of expanded keyword strings.
    """
    modifiers_prefix = [
        "como", "o que é", "porque", "quando", "quanto custa",
        "melhor", "qual",
    ]
    modifiers_suffix = [
        "sintomas", "tratamento", "causas", "como funciona",
        "preço", "online", "perto de mim", "funciona",
    ]

    expanded = []
    for mod in modifiers_prefix:
        expanded.append(f"{mod} {keyword}")
    for mod in modifiers_suffix:
        expanded.append(f"{keyword} {mod}")

    return expanded


def discover_keywords(seed_keyword, existing_keywords=None, max_results=30):
    """Discover new keyword opportunities from multiple sources.

    Sources:
    1. Google Suggest (autocomplete)
    2. SERP Related Searches (via SerperAPI)
    3. SERP People Also Ask (via SerperAPI)
    4. Modifier expansion

    Args:
        seed_keyword: Starting keyword to expand from.
        existing_keywords: Set of keywords already covered (to filter out).
        max_results: Maximum keywords to return.

    Returns:
        List of dicts: [{"keyword": str, "source": str, "priority": int}]
    """
    existing = {kw.lower().strip() for kw in (existing_keywords or [])}
    all_keywords = {}  # keyword_lower → {"keyword": str, "source": str, "score": int}

    # Source 1: Google Suggest
    suggestions = google_suggest(seed_keyword)
    for s in suggestions:
        kl = s.lower().strip()
        if kl not in existing and kl not in all_keywords:
            all_keywords[kl] = {"keyword": s, "source": "google_suggest", "score": 3}

    # Source 2 & 3: SERP data
    serp = generate_serp_brief(seed_keyword)
    if serp:
        for related in serp.get("related_searches", []):
            kl = related.lower().strip()
            if kl not in existing and kl not in all_keywords:
                all_keywords[kl] = {"keyword": related, "source": "serp_related", "score": 4}

        for paa in serp.get("people_also_ask", []):
            q = paa.get("question", "")
            kl = q.lower().strip()
            if kl and kl not in existing and kl not in all_keywords:
                all_keywords[kl] = {"keyword": q, "source": "people_also_ask", "score": 5}

    # Source 4: Modifier expansion
    expanded = expand_with_modifiers(seed_keyword)
    # Validate expanded keywords via Google Suggest
    for exp_kw in expanded[:10]:
        sub_suggestions = google_suggest(exp_kw)
        for s in sub_suggestions[:3]:
            kl = s.lower().strip()
            if kl not in existing and kl not in all_keywords:
                all_keywords[kl] = {"keyword": s, "source": "modifier_expansion", "score": 2}

    # Sort by score (higher = better source) and limit
    results = sorted(all_keywords.values(), key=lambda x: x["score"], reverse=True)
    results = results[:max_results]

    logger.info("Keyword discovery for '%s': %d new keywords found (from %d total candidates)",
                seed_keyword, len(results), len(all_keywords))

    return results
