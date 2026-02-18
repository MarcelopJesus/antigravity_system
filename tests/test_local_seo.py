"""Tests for SEO Local Enhancement in prompts and agents."""
import unittest


class TestLocalSeoConfig(unittest.TestCase):

    def test_sites_json_has_local_seo(self):
        import json
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
        site = sites[0]
        assert 'local_seo' in site
        assert site['local_seo']['neighborhood'] == 'Moema'
        assert site['local_seo']['city'] == 'São Paulo'
        assert len(site['local_seo']['local_keywords']) >= 1


class TestAnalystLocalSeo(unittest.TestCase):

    def test_analyst_prompt_includes_local_seo(self):
        """When site_config has local_seo, the prompt should contain location info."""
        from config.prompts import CONTENT_ANALYST_PROMPT
        local_seo_section = (
            "7. SEO LOCAL (se aplicável):\n"
            "   - Localização do profissional: Moema, São Paulo\n"
            "   - Mencione a localização naturalmente no outline (pelo menos 1 seção com referência local)\n"
            "   - Inclua termos locais nas keyword_variations quando relevante: Hipnoterapia Moema"
        )
        prompt = CONTENT_ANALYST_PROMPT.format(
            keyword="teste",
            links_list="",
            knowledge_base="",
            local_seo_section=local_seo_section,
        )
        assert "Moema, São Paulo" in prompt
        assert "SEO LOCAL" in prompt

    def test_analyst_prompt_without_local_seo(self):
        from config.prompts import CONTENT_ANALYST_PROMPT
        prompt = CONTENT_ANALYST_PROMPT.format(
            keyword="teste",
            links_list="",
            knowledge_base="",
            local_seo_section="",
        )
        assert "teste" in prompt


class TestWriterLocalSeo(unittest.TestCase):

    def test_writer_prompt_includes_location(self):
        from config.prompts import SENIOR_WRITER_PROMPT
        local_seo_section = "LOCALIZAÇÃO DO PROFISSIONAL: Moema, São Paulo"
        prompt = SENIOR_WRITER_PROMPT.format(
            outline_json="{}",
            keyword_variations="N/A",
            lsi_keywords="N/A",
            knowledge_base="",
            local_seo_section=local_seo_section,
        )
        assert "Moema, São Paulo" in prompt


if __name__ == "__main__":
    unittest.main()
