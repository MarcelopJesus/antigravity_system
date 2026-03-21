"""Tests for Story 5.3 — Performance Dashboard."""
import json
import pytest
from unittest.mock import MagicMock, patch
from core.dashboard.dashboard import PerformanceDashboard


class TestDashboard:

    def test_generate_report_no_clients(self):
        dashboard = PerformanceDashboard()
        report = dashboard.generate_report()
        assert "generated_at" in report
        assert "summary" in report
        assert report["summary"]["total_articles"] == 0

    def test_generate_report_with_wp(self):
        wp = MagicMock()
        wp.get_posts.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        dashboard = PerformanceDashboard(wp_client=wp)
        report = dashboard.generate_report()
        assert report["articles"]["total"] == 3

    def test_save_json_report(self, tmp_path):
        dashboard = PerformanceDashboard()
        filepath = str(tmp_path / "report.json")
        dashboard.save_json_report(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert "summary" in data


class TestConversionTracking:
    """Test Story 5.4 — WhatsApp UTM tracking."""

    def test_cta_with_slug_tracking(self):
        from core.tenant_config import TenantConfig
        tc = TenantConfig({
            "company_id": "test",
            "site_name": "Test",
            "wordpress_url": "https://test.com",
            "spreadsheet_id": "x",
            "cta": {
                "type": "whatsapp",
                "url": "https://wa.me/message/ABC",
                "text": "Falar no WhatsApp",
                "box_text": "Agende",
            }
        })
        html = tc.get_cta_html(slug="ansiedade-generalizada")
        assert "text=Vim+do+artigo+ansiedade-generalizada" in html

    def test_cta_without_slug(self):
        from core.tenant_config import TenantConfig
        tc = TenantConfig({
            "company_id": "test",
            "site_name": "Test",
            "wordpress_url": "https://test.com",
            "spreadsheet_id": "x",
            "cta": {
                "type": "whatsapp",
                "url": "https://wa.me/message/ABC",
                "text": "Falar",
                "box_text": "",
            }
        })
        html = tc.get_cta_html()
        assert "text=" not in html
