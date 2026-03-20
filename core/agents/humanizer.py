"""HumanizerAgent — Transforms content into authentic voice."""
from core.agents.base import BaseAgent


class HumanizerAgent(BaseAgent):
    name = "humanizer"

    def _build_prompt(self, input_data):
        draft_html = input_data
        voice_guide = ""

        # Load voice guide from cache or KB
        if self.kb_cache and self.tenant_config:
            voice_guide = self.kb_cache.get_voice_guide(
                self.tenant_config.company_id,
                self.tenant_config.kb_path
            )
        elif self.kb:
            voice_guide = self.kb.load_voice_guide()

        # Use PromptEngine if available
        if self.prompt_engine:
            return self.prompt_engine.render("humanizer", {
                "draft_html": draft_html,
                "voice_guide": voice_guide,
            })

        # Fallback to hardcoded prompts
        from config.prompts import TRI_HUMANIZER_PROMPT
        return TRI_HUMANIZER_PROMPT.format(
            voice_guide=voice_guide,
            draft_html=draft_html,
        )

    def _parse_response(self, raw_text, input_data=None):
        return self.clean_llm_output(raw_text)
