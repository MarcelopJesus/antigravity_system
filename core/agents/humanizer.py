"""HumanizerAgent — Transforms content into authentic Marcelo Jesus voice."""
from core.agents.base import BaseAgent
from config.prompts import TRI_HUMANIZER_PROMPT


class HumanizerAgent(BaseAgent):
    name = "humanizer"

    def _build_prompt(self, input_data):
        draft_html = input_data
        voice_guide = ""
        if self.kb:
            voice_guide = self.kb.load_voice_guide()

        return TRI_HUMANIZER_PROMPT.format(
            voice_guide=voice_guide,
            draft_html=draft_html,
        )

    def _parse_response(self, raw_text, input_data=None):
        return self.clean_llm_output(raw_text)
