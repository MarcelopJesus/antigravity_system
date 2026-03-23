"""WriterAgent — Writes the full article based on the outline."""
import json
from core.agents.base import BaseAgent


class WriterAgent(BaseAgent):
    name = "writer"

    def _get_kb_filter(self):
        return ["tri_essencia", "premium", "voz"]

    def _build_prompt(self, input_data):
        if isinstance(input_data, dict) and '_site_config' in input_data:
            site_config = input_data.pop('_site_config')
            outline_json = input_data
        else:
            site_config = {}
            outline_json = input_data

        kb_text = self._load_kb()

        keyword_variations = outline_json.get('keyword_variations', [])
        lsi_keywords = outline_json.get('lsi_keywords', [])

        # Use PromptEngine if available
        if self.prompt_engine:
            return self.prompt_engine.render("writer", {
                "outline_json": json.dumps(outline_json, indent=2, ensure_ascii=False),
                "keyword_variations": ', '.join(keyword_variations) if keyword_variations else 'N/A',
                "lsi_keywords": ', '.join(lsi_keywords) if lsi_keywords else 'N/A',
                "knowledge_base": kb_text,
            })

        # Fallback to hardcoded prompts
        from config.prompts import SENIOR_WRITER_PROMPT
        local_seo = site_config.get("local_seo", {}) if site_config else {}
        if local_seo:
            local_seo_section = (
                f"LOCALIZAÇÃO DO PROFISSIONAL: {local_seo.get('primary_location', '')}\n"
                f"   - Mencione a localização naturalmente no texto (2-3 vezes no artigo)\n"
                f"   - Inclua referência ao consultório quando fizer sentido contextual"
            )
        else:
            local_seo_section = ""

        return SENIOR_WRITER_PROMPT.format(
            outline_json=json.dumps(outline_json, indent=2, ensure_ascii=False),
            keyword_variations=', '.join(keyword_variations) if keyword_variations else 'N/A',
            lsi_keywords=', '.join(lsi_keywords) if lsi_keywords else 'N/A',
            knowledge_base=kb_text,
            local_seo_section=local_seo_section,
        )

    def _parse_response(self, raw_text, input_data=None):
        clean = self.clean_llm_output(raw_text)

        # Strip markdown code blocks if model wrapped HTML in them
        if clean.strip().startswith("```"):
            import re
            clean = re.sub(r'^```(?:html)?\s*', '', clean.strip())
            clean = re.sub(r'\s*```\s*$', '', clean)

        return clean.strip()
