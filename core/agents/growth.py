"""GrowthAgent — Generates cluster maps and topic suggestions."""
from core.agents.base import BaseAgent
from core.logger import get_logger

logger = get_logger(__name__)


class GrowthAgent(BaseAgent):
    name = "growth"

    def _build_prompt(self, input_data):
        title = input_data["title"]

        # Use PromptEngine if available
        if self.prompt_engine:
            return self.prompt_engine.render("growth", {
                "title": title,
            })

        # Fallback to hardcoded prompts
        from config.prompts import GROWTH_HACKER_PROMPT
        return GROWTH_HACKER_PROMPT.format(title=title)

    def _parse_response(self, raw_text, input_data=None):
        """Parse cluster map or simple suggestions from response."""
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        # Check if response has PILLAR/CLUSTER format
        has_cluster_format = any(
            line.upper().startswith(("PILLAR:", "CLUSTER:"))
            for line in lines
        )

        if has_cluster_format:
            return _parse_cluster_map(lines)

        # Fallback: simple suggestions (backward compatible)
        suggestions = [
            line.replace("-", "").strip()
            for line in lines
            if line.strip()
        ]
        return suggestions[:2]


def _parse_cluster_map(lines):
    """Parse PILLAR/CLUSTER format into structured list.

    Returns:
        List of dicts: [{"keyword": str, "type": "pillar"|"cluster"}]
    """
    result = []
    for line in lines:
        upper = line.upper()
        if upper.startswith("PILLAR:"):
            kw = line[7:].strip()
            if kw:
                result.append({"keyword": kw, "type": "pillar"})
        elif upper.startswith("CLUSTER:"):
            kw = line[8:].strip()
            if kw:
                result.append({"keyword": kw, "type": "cluster"})

    logger.info("Cluster map parsed: %d pillar(s), %d cluster(s)",
                sum(1 for r in result if r["type"] == "pillar"),
                sum(1 for r in result if r["type"] == "cluster"))
    return result
