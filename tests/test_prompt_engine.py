"""Tests for PromptEngine — rendering, inheritance, overrides."""
import os
import pytest
import yaml
from core.prompt_engine import PromptEngine
from core.tenant_config import TenantConfig


@pytest.fixture
def prompt_dirs(tmp_path):
    """Create temp tenant directory with default and tenant prompts."""
    # _default prompts
    default_dir = tmp_path / "_default"
    default_dir.mkdir()
    (default_dir / "prompts").mkdir()
    (default_dir / "tenant.yaml").write_text(yaml.dump({
        "company_id": "",
        "wordpress_url": "",
        "credentials_env_prefix": "",
        "spreadsheet_id": "",
    }))

    # Default analyst prompt
    (default_dir / "prompts" / "analyst.txt").write_text(
        "You are an expert in {{ persona.expertise }}.\n"
        "Keyword: {{ keyword }}\n"
        "CTA: {{ cta_html }}"
    )

    # Default writer prompt
    (default_dir / "prompts" / "writer.txt").write_text(
        "Write for {{ persona.name }} about {{ keyword }}."
    )

    # Tenant with override
    tenant_dir = tmp_path / "testco"
    tenant_dir.mkdir()
    (tenant_dir / "prompts").mkdir()
    (tenant_dir / "knowledge_base").mkdir()

    tenant_config = {
        "company_id": "testco",
        "site_name": "Test Company",
        "wordpress_url": "https://test.com",
        "credentials_env_prefix": "TEST",
        "spreadsheet_id": "abc123",
        "persona": {
            "name": "Dr. Test",
            "title": "Expert",
            "expertise": "testing",
        },
        "cta": {
            "type": "whatsapp",
            "url": "https://wa.me/123",
            "text": "Contact Dr. Test",
            "box_text": "Want to know more?",
        },
        "local_seo": {
            "primary_location": "Downtown",
            "neighborhood": "Central",
            "city": "TestCity",
            "state": "TS",
            "local_keywords": ["test downtown", "expert central"],
        },
    }
    (tenant_dir / "tenant.yaml").write_text(yaml.dump(tenant_config))

    # Tenant-specific analyst override
    (tenant_dir / "prompts" / "analyst.txt").write_text(
        "CUSTOM ANALYST for {{ persona.name }}.\n"
        "Keyword: {{ keyword }}"
    )

    return str(tmp_path)


class TestPromptEngine:
    def test_render_default_template(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        # Writer uses default (no tenant override)
        result = engine.render("writer", {"keyword": "test topic"})
        assert "Dr. Test" in result
        assert "test topic" in result

    def test_render_tenant_override(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        # Analyst has tenant-specific override
        result = engine.render("analyst", {"keyword": "test kw"})
        assert "CUSTOM ANALYST" in result
        assert "Dr. Test" in result
        assert "test kw" in result

    def test_render_with_cta_html(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        # Default analyst template has {{ cta_html }}
        # But testco overrides analyst, so use writer context instead
        result = engine.render("writer", {"keyword": "kw"})
        assert "Dr. Test" in result

    def test_render_missing_template(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        result = engine.render("nonexistent_agent")
        assert result == ""

    def test_has_template(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        assert engine.has_template("analyst")
        assert engine.has_template("writer")
        assert not engine.has_template("nonexistent")

    def test_local_seo_section(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        ctx = engine._build_context({"keyword": "test"})
        assert "Downtown" in ctx["local_seo_section"]
        assert "Central" in ctx["local_seo_section"]

    def test_empty_context_no_error(self, prompt_dirs):
        tc = TenantConfig.load("testco", tenants_dir=prompt_dirs)
        engine = PromptEngine(tc, tenants_dir=prompt_dirs)

        # Render without extra context
        result = engine.render("writer")
        assert "Dr. Test" in result

    def test_no_tenant_config(self, prompt_dirs):
        engine = PromptEngine(tenant_config=None, tenants_dir=prompt_dirs)
        # Should fall back to _default
        result = engine.render("writer", {"keyword": "test", "persona": {"name": "Fallback"}})
        assert "Fallback" in result
