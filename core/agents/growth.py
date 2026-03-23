"""GrowthAgent — Generates cluster maps and topic suggestions."""
from core.agents.base import BaseAgent
from core.logger import get_logger

logger = get_logger(__name__)


class GrowthAgent(BaseAgent):
    name = "growth"

    def _build_prompt(self, input_data):
        title = input_data["title"]
        existing = input_data.get("existing_keywords", "")

        # Use PromptEngine if available
        if self.prompt_engine:
            return self.prompt_engine.render("growth", {
                "title": title,
                "existing_keywords": existing if existing else "(nenhuma ainda)",
            })

        # Fallback to hardcoded prompts
        from config.prompts import GROWTH_HACKER_PROMPT
        return GROWTH_HACKER_PROMPT.format(title=title)

    def _parse_response(self, raw_text, input_data=None):
        """Parse cluster-aware suggestions from response."""
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        # New format: CLUSTER: name + KEYWORD: keyword
        has_new_format = any(
            line.upper().startswith(("KEYWORD:", "CLUSTER:"))
            for line in lines
        )

        if has_new_format:
            return _parse_cluster_keywords(lines)

        # Legacy format: PILLAR/CLUSTER
        has_legacy = any(
            line.upper().startswith("PILLAR:")
            for line in lines
        )
        if has_legacy:
            return _parse_cluster_map(lines)

        # Fallback: plain text suggestions
        suggestions = [
            line.replace("-", "").strip()
            for line in lines
            if line.strip() and len(line.strip()) > 3
        ]
        return suggestions[:6]


def _parse_cluster_keywords(lines):
    """Parse CLUSTER/KEYWORD format into list of keyword strings.

    Returns:
        List of max 3 keyword strings (plain, ready for sheets).
    """
    cluster_name = ""
    keywords = []

    for line in lines:
        upper = line.upper()
        if upper.startswith("CLUSTER:"):
            cluster_name = line[8:].strip()
        elif upper.startswith("KEYWORD:"):
            kw = line[8:].strip()
            if kw and len(kw.split()) <= 6:
                keywords.append(kw)

    # Hard limit: max 3 suggestions per article
    keywords = keywords[:3]

    logger.info("Growth suggestions: %d keywords (cluster: %s)",
                len(keywords), cluster_name or "unknown")
    return keywords


def _parse_cluster_map(lines):
    """Parse legacy PILLAR/CLUSTER format. Returns list of keyword strings."""
    keywords = []
    for line in lines:
        upper = line.upper()
        if upper.startswith("PILLAR:"):
            kw = line[7:].strip()
            if kw:
                keywords.append(kw)
        elif upper.startswith("CLUSTER:"):
            kw = line[8:].strip()
            if kw:
                keywords.append(kw)
    return keywords
