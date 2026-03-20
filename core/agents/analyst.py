"""AnalystAgent — Creates the strategic outline (JSON)."""
import json
import re
from core.agents.base import BaseAgent, AgentResult
from core.logger import get_logger

logger = get_logger(__name__)

MAX_ANALYST_RETRIES = 2


class AnalystAgent(BaseAgent):
    name = "analyst"

    def _get_json_mode(self):
        return True

    def _get_kb_filter(self):
        return ["tri_essencia", "premium"]

    def _build_prompt(self, input_data):
        keyword = input_data["keyword"]
        links_inventory = input_data.get("links_inventory", [])
        site_config = input_data.get("site_config", {})
        kb_text = self._load_kb()

        if isinstance(links_inventory, list):
            links_text = "\n".join(
                [f"- {item.get('keyword', 'Link')}: {item.get('url', '#')}" for item in links_inventory]
            )
        else:
            links_text = str(links_inventory)

        # Use PromptEngine if available
        if self.prompt_engine:
            local_seo = {}
            if self.tenant_config:
                local_seo = self.tenant_config.get_local_seo()
            local_seo_section = ""
            if local_seo and local_seo.get("primary_location"):
                local_seo_section = (
                    f"7. SEO LOCAL (se aplicável):\n"
                    f"   - Localização do profissional: {local_seo.get('primary_location', '')}\n"
                    f"   - Mencione a localização naturalmente no outline\n"
                    f"   - Inclua termos locais: {', '.join(local_seo.get('local_keywords', []))}"
                )
            return self.prompt_engine.render("analyst", {
                "keyword": keyword,
                "links_list": links_text,
                "knowledge_base": kb_text,
                "local_seo_section": local_seo_section,
            })

        # Fallback to hardcoded prompts
        from config.prompts import CONTENT_ANALYST_PROMPT
        local_seo = site_config.get("local_seo", {}) if site_config else {}
        if local_seo:
            local_seo_section = (
                f"7. SEO LOCAL (se aplicável):\n"
                f"   - Localização do profissional: {local_seo.get('primary_location', '')}\n"
                f"   - Mencione a localização naturalmente no outline (pelo menos 1 seção com referência local)\n"
                f"   - Inclua termos locais nas keyword_variations quando relevante: {', '.join(local_seo.get('local_keywords', []))}"
            )
        else:
            local_seo_section = ""

        return CONTENT_ANALYST_PROMPT.format(
            keyword=keyword,
            links_list=links_text,
            knowledge_base=kb_text,
            local_seo_section=local_seo_section,
        )

    def _parse_response(self, raw_text, input_data=None):
        """Parse JSON from LLM response with robust extraction."""
        # Attempt 1: Direct parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Attempt 2: Strip markdown code blocks
        cleaned = raw_text.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Attempt 3: Find JSON object in text via brace matching
        start = raw_text.find('{')
        if start >= 0:
            depth = 0
            for i in range(start, len(raw_text)):
                if raw_text[i] == '{':
                    depth += 1
                elif raw_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw_text[start:i + 1])
                        except json.JSONDecodeError:
                            break

        raise json.JSONDecodeError(
            f"Could not extract valid JSON from analyst response ({len(raw_text)} chars)",
            raw_text[:200], 0
        )

    def execute(self, input_data) -> AgentResult:
        """Execute with retry logic for JSON parsing failures."""
        last_result = None
        for attempt in range(1, MAX_ANALYST_RETRIES + 1):
            result = super().execute(input_data)
            if result.success:
                return result
            last_result = result
            if attempt < MAX_ANALYST_RETRIES:
                logger.warning(
                    "[analyst] Attempt %d/%d failed: %s — retrying...",
                    attempt, MAX_ANALYST_RETRIES, result.error
                )
        logger.error("[analyst] All %d attempts failed.", MAX_ANALYST_RETRIES)
        return last_result
