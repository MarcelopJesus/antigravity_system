"""GrowthAgent — Scans content for gaps and suggests new topics."""
from core.agents.base import BaseAgent
from config.prompts import GROWTH_HACKER_PROMPT


class GrowthAgent(BaseAgent):
    name = "growth"

    def _build_prompt(self, input_data):
        title = input_data["title"]
        return GROWTH_HACKER_PROMPT.format(title=title)

    def _parse_response(self, raw_text, input_data=None):
        suggestions = [
            line.strip().replace("-", "").strip()
            for line in raw_text.split('\n')
            if line.strip()
        ]
        return suggestions[:2]
