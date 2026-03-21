"""Content Gap Analyzer — Identifies keyword opportunities from SERP data."""
from core.logger import get_logger

logger = get_logger(__name__)


def find_content_gaps(serp_brief, existing_keywords):
    """Compare SERP related searches against existing article keywords.

    Args:
        serp_brief: SERP brief dict from serp_analyzer.
        existing_keywords: Set/list of keywords already covered (from inventory).

    Returns:
        List of gap keyword dicts: [{"keyword": str, "source": str}]
    """
    if not serp_brief:
        return []

    existing_lower = {kw.lower().strip() for kw in existing_keywords if kw}
    gaps = []

    # Check related searches
    for related in serp_brief.get("related_searches", []):
        if related.lower().strip() not in existing_lower:
            gaps.append({
                "keyword": related,
                "source": "related_search",
            })

    # Check PAA questions as potential keywords
    for paa in serp_brief.get("people_also_ask", []):
        question = paa.get("question", "")
        if question and question.lower().strip() not in existing_lower:
            gaps.append({
                "keyword": question,
                "source": "people_also_ask",
            })

    logger.info("Content gap analysis: %d gaps found (%d related, %d PAA)",
                len(gaps),
                sum(1 for g in gaps if g["source"] == "related_search"),
                sum(1 for g in gaps if g["source"] == "people_also_ask"))

    return gaps
