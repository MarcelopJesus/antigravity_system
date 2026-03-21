"""Semantic Entity Mapping — Queries Knowledge Graph for topic entities."""
import os
import requests
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv(override=True)

logger = get_logger(__name__)

KG_API_URL = "https://kgsearch.googleapis.com/v1/entities:search"


def search_entities(query, api_key=None, language="pt", limit=5):
    """Search Google Knowledge Graph for entities related to a query.

    Args:
        query: Search query (keyword/topic).
        api_key: Google API key (falls back to KNOWLEDGE_GRAPH_API_KEY env var).
        language: Language code.
        limit: Max entities to return.

    Returns:
        List of entity dicts: [{"name": str, "type": str, "description": str}]
        Empty list on failure.
    """
    key = api_key or os.getenv("KNOWLEDGE_GRAPH_API_KEY", "")
    if not key:
        # Fallback: use GOOGLE_API_KEYS (same keys used for Gemini)
        from config.settings import GOOGLE_API_KEYS_LIST
        if GOOGLE_API_KEYS_LIST:
            key = GOOGLE_API_KEYS_LIST[0]

    if not key:
        logger.info("No Knowledge Graph API key. Entity mapping skipped.")
        return []

    params = {
        "query": query,
        "key": key,
        "limit": limit,
        "indent": True,
        "languages": language,
    }

    try:
        response = requests.get(KG_API_URL, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning("Knowledge Graph API error (status=%d)", response.status_code)
            return []

        data = response.json()
        return _parse_kg_response(data)

    except requests.RequestException as e:
        logger.warning("Knowledge Graph API request failed: %s", e)
        return []


def _parse_kg_response(data):
    """Parse Knowledge Graph API response into entity list."""
    entities = []

    for element in data.get("itemListElement", []):
        result = element.get("result", {})
        name = result.get("name", "")
        types = result.get("@type", [])
        description = result.get("description", "")
        detail_desc = result.get("detailedDescription", {}).get("articleBody", "")

        if name:
            entities.append({
                "name": name,
                "types": types if isinstance(types, list) else [types],
                "description": description,
                "detail": detail_desc[:200] if detail_desc else "",
                "score": element.get("resultScore", 0),
            })

    entities.sort(key=lambda x: x["score"], reverse=True)
    return entities


def get_expected_entities_for_keyword(keyword, api_key=None):
    """Get a list of entity names expected for a keyword/topic.

    This is used by the SEO Scorer's entity coverage check.
    Falls back to empty list if API is unavailable.

    Returns:
        List of entity name strings.
    """
    entities = search_entities(keyword, api_key=api_key)
    return [e["name"] for e in entities if e["name"]]
