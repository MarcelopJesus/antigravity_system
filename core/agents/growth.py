"""GrowthAgent — Scans content for gaps and suggests new topics."""
from core.agents.base import BaseAgent


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
        suggestions = [
            line.strip().replace("-", "").strip()
            for line in raw_text.split('\n')
            if line.strip()
        ]
        return suggestions[:2]
