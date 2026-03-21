"""AnalystAgent — Creates the strategic outline (JSON)."""
import json
import re
from core.agents.base import BaseAgent, AgentResult
from core.logger import get_logger

logger = get_logger(__name__)

MAX_ANALYST_RETRIES = 2


def _format_serp_section(serp_brief):
    """Format SERP brief data into a section for the analyst prompt."""
    if not serp_brief:
        return ""

    lines = ["═══════════════════════════════════════════════",
             "INTELIGÊNCIA COMPETITIVA (dados reais do Google):",
             "═══════════════════════════════════════════════"]

    # Top competitor titles
    titles = serp_brief.get("competitor_titles", [])
    if titles:
        lines.append("\nTÍTULOS DOS TOP 5 RESULTADOS:")
        for i, t in enumerate(titles[:5], 1):
            lines.append(f"  {i}. {t}")

    # Recommended word count
    rwc = serp_brief.get("recommended_word_count", 0)
    if rwc:
        lines.append(f"\nMETA DE PALAVRAS RECOMENDADA: {rwc} (20% acima da média dos top 10)")

    # People Also Ask
    paa = serp_brief.get("people_also_ask", [])
    if paa:
        lines.append("\nPERGUNTAS REAIS DO GOOGLE (People Also Ask):")
        for item in paa[:6]:
            lines.append(f"  - {item.get('question', '')}")
        lines.append("  → USE estas perguntas na seção FAQ do outline!")

    # Related searches
    related = serp_brief.get("related_searches", [])
    if related:
        lines.append("\nBUSCAS RELACIONADAS:")
        for r in related[:8]:
            lines.append(f"  - {r}")

    lines.append("═══════════════════════════════════════════════")
    return "\n".join(lines)


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
        serp_brief = input_data.get("serp_brief", {})
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
            # Build SERP section for prompt
            serp_section = _format_serp_section(serp_brief)

            return self.prompt_engine.render("analyst", {
                "keyword": keyword,
                "links_list": links_text,
                "knowledge_base": kb_text,
                "local_seo_section": local_seo_section,
                "serp_section": serp_section,
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
            parsed = json.loads(raw_text)
            # If model returned a list, extract first element
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]
            return parsed
        except json.JSONDecodeError:
            pass

        # Attempt 2: Strip markdown code blocks
        cleaned = raw_text.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]
            return parsed
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
