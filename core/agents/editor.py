"""EditorAgent — Polishes content, checks constraints and HTML structure."""
import markdown
from core.agents.base import BaseAgent
from core.logger import get_logger

logger = get_logger(__name__)


class EditorAgent(BaseAgent):
    name = "editor"

    def _build_prompt(self, input_data):
        draft_html = input_data

        # Use PromptEngine if available
        if self.prompt_engine:
            return self.prompt_engine.render("editor", {
                "draft_html": draft_html,
            })

        # Fallback to hardcoded prompts
        from config.prompts import CONVERSION_EDITOR_PROMPT
        return CONVERSION_EDITOR_PROMPT.format(draft_html=draft_html)

    def _parse_response(self, raw_text, input_data=None):
        clean_text = self.clean_llm_output(raw_text)

        # Remove conversational prefixes
        if "<h1>" in clean_text:
            clean_text = clean_text[clean_text.find("<h1>"):]

        # SAFETY NET: If text still looks like Markdown, force convert
        if "##" in clean_text or "**" in clean_text:
            logger.warning("Detected raw Markdown in editor output. Converting to HTML...")
            html = markdown.markdown(clean_text)
            return html.strip()

        return clean_text.strip()
