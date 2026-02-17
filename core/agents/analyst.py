"""AnalystAgent — Creates the strategic outline (JSON)."""
import json
from core.agents.base import BaseAgent
from config.prompts import CONTENT_ANALYST_PROMPT


class AnalystAgent(BaseAgent):
    name = "analyst"

    def _get_json_mode(self):
        return True

    def _get_kb_filter(self):
        return ["tri_essencia", "premium"]

    def _build_prompt(self, input_data):
        keyword = input_data["keyword"]
        links_inventory = input_data.get("links_inventory", [])
        kb_text = self._load_kb()

        if isinstance(links_inventory, list):
            links_text = "\n".join(
                [f"- {item.get('keyword', 'Link')}: {item.get('url', '#')}" for item in links_inventory]
            )
        else:
            links_text = str(links_inventory)

        return CONTENT_ANALYST_PROMPT.format(
            keyword=keyword,
            links_list=links_text,
            knowledge_base=kb_text,
        )

    def _parse_response(self, raw_text, input_data=None):
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            cleaned = raw_text.replace("```json", "").replace("```", "")
            return json.loads(cleaned)
