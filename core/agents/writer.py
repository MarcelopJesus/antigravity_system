"""WriterAgent — Writes the full article based on the outline."""
import json
from core.agents.base import BaseAgent
from config.prompts import SENIOR_WRITER_PROMPT


class WriterAgent(BaseAgent):
    name = "writer"

    def _get_kb_filter(self):
        return ["tri_essencia", "premium"]

    def _build_prompt(self, input_data):
        outline_json = input_data
        kb_text = self._load_kb()

        return SENIOR_WRITER_PROMPT.format(
            outline_json=json.dumps(outline_json, indent=2, ensure_ascii=False),
            knowledge_base=kb_text,
        )

    def _parse_response(self, raw_text, input_data=None):
        return raw_text
