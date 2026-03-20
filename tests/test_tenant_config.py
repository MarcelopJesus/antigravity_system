"""Tests for TenantConfig — load, validate, merge, backward compat."""
import os
import pytest
import tempfile
import yaml
from core.tenant_config import TenantConfig, TenantConfigError


@pytest.fixture
def tenant_dir(tmp_path):
    """Create a temp tenant directory with _default and a test tenant."""
    # _default
    default_dir = tmp_path / "_default"
    default_dir.mkdir()
    default_config = {
        "company_id": "",
        "site_name": "",
        "wordpress_url": "",
        "credentials_env_prefix": "",
        "spreadsheet_id": "",
        "agents": {
            "enabled": ["analyst", "writer", "humanizer", "editor", "visual", "growth"],
            "config": {"analyst": {"max_retries": 3}},
        },
        "schedule": {
            "frequency": "twice_daily",
            "times": ["09:00", "21:00"],
            "timezone": "America/Sao_Paulo",
            "max_articles_per_run": 1,
        },
        "seo": {"min_score": 40, "max_internal_links": 5},
        "cta": {
            "type": "whatsapp",
            "url": "",
            "text": "Fale conosco",
            "box_text": "Entre em contato.",
        },
    }
    with open(default_dir / "tenant.yaml", "w") as f:
        yaml.dump(default_config, f)

    # mjesus tenant
    tenant = tmp_path / "mjesus"
    tenant.mkdir()
    (tenant / "knowledge_base").mkdir()
    tenant_config = {
        "company_id": "mjesus",
        "site_name": "Marcelo Jesus",
        "wordpress_url": "https://mjesus.com.br",
        "credentials_env_prefix": "MJESUS",
        "spreadsheet_id": "abc123",
        "cta": {
            "type": "whatsapp",
            "url": "https://wa.me/5511999",
            "text": "Falar com Marcelo",
            "box_text": "Quer saber mais?",
        },
        "persona": {
            "name": "Marcelo Jesus",
            "title": "Terapeuta TRI",
            "expertise": "hipnoterapia",
        },
        "agents": {
            "enabled": ["analyst", "writer", "editor"],  # No humanizer/visual/growth
        },
    }
    with open(tenant / "tenant.yaml", "w") as f:
        yaml.dump(tenant_config, f)

    return str(tmp_path)


class TestTenantConfig:
    def test_load_merges_with_default(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        assert tc.company_id == "mjesus"
        assert tc.wordpress_url == "https://mjesus.com.br"
        # Inherited from _default
        assert tc.get_seo_config()["min_score"] == 40
        # Overridden by tenant
        assert tc.get_cta()["url"] == "https://wa.me/5511999"

    def test_load_missing_tenant_raises(self, tenant_dir):
        with pytest.raises(TenantConfigError, match="not found"):
            TenantConfig.load("nonexistent", tenants_dir=tenant_dir)

    def test_load_missing_required_fields(self, tenant_dir):
        # Create tenant with missing fields
        bad_dir = os.path.join(tenant_dir, "bad_tenant")
        os.makedirs(bad_dir)
        with open(os.path.join(bad_dir, "tenant.yaml"), "w") as f:
            yaml.dump({"company_id": "bad_tenant"}, f)

        with pytest.raises(TenantConfigError, match="missing required"):
            TenantConfig.load("bad_tenant", tenants_dir=tenant_dir)

    def test_list_all(self, tenant_dir):
        tenants = TenantConfig.list_all(tenants_dir=tenant_dir)
        assert "mjesus" in tenants
        assert "_default" not in tenants

    def test_get_enabled_agents(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        agents = tc.get_enabled_agents()
        assert "analyst" in agents
        assert "writer" in agents
        assert "humanizer" not in agents  # Overridden
        assert "visual" not in agents

    def test_get_agent_config_inherits_default(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        analyst_config = tc.get_agent_config("analyst")
        assert analyst_config.get("max_retries") == 3

    def test_get_cta(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        cta = tc.get_cta()
        assert cta["type"] == "whatsapp"
        assert "wa.me" in cta["url"]

    def test_get_cta_html(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        html = tc.get_cta_html()
        assert 'class="cta-box"' in html
        assert 'class="btn-whatsapp"' in html
        assert "wa.me" in html

    def test_get_schedule(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        schedule = tc.get_schedule()
        assert schedule["frequency"] == "twice_daily"
        assert schedule["max_articles_per_run"] == 1

    def test_get_persona(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        persona = tc.get_persona()
        assert persona["name"] == "Marcelo Jesus"

    def test_kb_path(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        assert tc.kb_path == "config/tenants/mjesus/knowledge_base"

    def test_to_site_config_backward_compat(self, tenant_dir):
        tc = TenantConfig.load("mjesus", tenants_dir=tenant_dir)
        site = tc.to_site_config()
        assert site["company_id"] == "mjesus"
        assert site["wordpress_url"] == "https://mjesus.com.br"

    def test_from_site_config(self):
        site = {
            "company_id": "test",
            "site_name": "Test Site",
            "wordpress_url": "https://test.com",
            "credentials_env_prefix": "TEST",
            "spreadsheet_id": "123",
            "author_name": "Author",
            "persona_prompt": "Expert",
        }
        tc = TenantConfig.from_site_config(site)
        assert tc.company_id == "test"
        assert tc.get_persona()["name"] == "Author"
        assert "analyst" in tc.get_enabled_agents()

    def test_list_all_empty_dir(self, tmp_path):
        tenants = TenantConfig.list_all(tenants_dir=str(tmp_path))
        assert tenants == []
