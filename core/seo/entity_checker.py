"""Entity coverage checker for SEO scoring.

Compares expected entities (from analyst outline) with entities
actually mentioned in the article text.
"""


def check_entity_coverage(text: str, expected_entities: list) -> dict:
    """Check how many expected entities appear in the article text.

    Args:
        text: Plain text of the article (no HTML).
        expected_entities: List of entity strings expected for the topic.

    Returns:
        dict with keys: found, total, ratio, missing
    """
    if not expected_entities:
        return {"found": 0, "total": 0, "ratio": 0.0, "missing": []}

    text_lower = text.lower()
    found = []
    missing = []

    for entity in expected_entities:
        if entity.lower() in text_lower:
            found.append(entity)
        else:
            missing.append(entity)

    total = len(expected_entities)
    ratio = len(found) / total if total > 0 else 0.0

    return {
        "found": len(found),
        "total": total,
        "ratio": ratio,
        "missing": missing,
    }
