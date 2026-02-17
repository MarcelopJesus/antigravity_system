"""GeminiBrain — Backward-compatible facade that delegates to modular agents."""
import json
import re
import markdown
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase
from core.agents.analyst import AnalystAgent
from core.agents.writer import WriterAgent
from core.agents.humanizer import HumanizerAgent
from core.agents.editor import EditorAgent
from core.agents.visual import VisualAgent
from core.agents.growth import GrowthAgent
from core.logger import get_logger

logger = get_logger(__name__)


class GeminiBrain:
    """Facade that maintains the original GeminiBrain interface.

    Internally delegates to modular agents and shared LLMClient/KnowledgeBase.
    All original methods preserved for backward compatibility.
    """

    def __init__(self, knowledge_base_path=None):
        self.knowledge_base_path = knowledge_base_path or "knowledge_base"

        # Shared infrastructure
        self.llm = LLMClient()
        self.kb = KnowledgeBase(self.knowledge_base_path)

        # Expose for backward compat
        self.api_keys = self.llm.api_keys
        self.current_key_index = self.llm.current_key_index

        # Agents
        self._analyst = AnalystAgent(self.llm, self.kb)
        self._writer = WriterAgent(self.llm, self.kb)
        self._humanizer = HumanizerAgent(self.llm, self.kb)
        self._editor = EditorAgent(self.llm, self.kb)
        self._visual = VisualAgent(self.llm, self.kb)
        self._growth = GrowthAgent(self.llm, self.kb)

    # --- Key management (delegated) ---

    def _configure_current_key(self):
        self.llm._configure_current_key()

    def _rotate_key(self):
        return self.llm._rotate_key()

    def _execute_with_retry(self, func, *args, **kwargs):
        return self.llm.execute_with_retry(func, *args, **kwargs)

    # --- Knowledge Base (delegated) ---

    def _load_knowledge_base(self, file_filter=None):
        return self.kb.load(file_filter=file_filter)

    def _load_voice_guide(self):
        return self.kb.load_voice_guide()

    # --- Agent methods (delegated) ---

    def analyze_and_plan(self, keyword, links_inventory):
        result = self._analyst.execute({"keyword": keyword, "links_inventory": links_inventory})
        if not result.success:
            raise Exception(f"Analyst agent failed: {result.error}")
        return result.content

    def write_article_body(self, outline_json):
        result = self._writer.execute(outline_json)
        if not result.success:
            raise Exception(f"Writer agent failed: {result.error}")
        return result.content

    def humanize_with_tri_voice(self, draft_html):
        result = self._humanizer.execute(draft_html)
        if not result.success:
            raise Exception(f"Humanizer agent failed: {result.error}")
        return result.content

    def edit_and_refine(self, draft_html):
        result = self._editor.execute(draft_html)
        if not result.success:
            raise Exception(f"Editor agent failed: {result.error}")
        return result.content

    def generate_image_prompts(self, final_article):
        result = self._visual.execute(final_article)
        if not result.success:
            raise Exception(f"Visual agent failed: {result.error}")
        return result.content

    def _is_valid_image(self, filepath):
        return VisualAgent._is_valid_image(filepath)

    def get_real_author_photo(self):
        return self._visual.get_real_author_photo(self.knowledge_base_path)

    def generate_final_images(self, image_prompt):
        return self._visual.generate_image(image_prompt)

    def identify_new_topics(self, title, final_article):
        result = self._growth.execute({"title": title})
        if not result.success:
            raise Exception(f"Growth agent failed: {result.error}")
        return result.content
