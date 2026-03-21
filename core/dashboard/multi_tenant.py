"""Multi-Tenant Dashboard — Unified view across all tenants."""
import json
import time
from core.tenant_config import TenantConfig
from core.dashboard.dashboard import PerformanceDashboard
from core.logger import get_logger

logger = get_logger(__name__)


class MultiTenantDashboard:
    """Aggregates dashboard data across all tenants."""

    def __init__(self):
        self.tenants = TenantConfig.list_all()

    def generate_unified_report(self, days=28):
        """Generate a report covering all tenants.

        Returns:
            dict with per-tenant reports and aggregated summary.
        """
        tenant_reports = {}
        totals = {
            "total_articles": 0,
            "total_clicks": 0,
            "total_impressions": 0,
            "tenants_count": 0,
        }

        for tenant_id in self.tenants:
            try:
                tc = TenantConfig.load(tenant_id)
                dashboard = PerformanceDashboard(
                    gsc_property_url=tc.wordpress_url,
                )
                report = dashboard.generate_report(days)
                tenant_reports[tenant_id] = report

                s = report.get("summary", {})
                totals["total_articles"] += s.get("total_articles", 0)
                totals["total_clicks"] += s.get("total_clicks", 0)
                totals["total_impressions"] += s.get("total_impressions", 0)
                totals["tenants_count"] += 1

            except Exception as e:
                logger.warning("Failed to generate report for tenant '%s': %s", tenant_id, e)
                tenant_reports[tenant_id] = {"error": str(e)}

        avg_ctr = (
            (totals["total_clicks"] / totals["total_impressions"] * 100)
            if totals["total_impressions"] > 0 else 0
        )

        return {
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "period_days": days,
            "tenants": tenant_reports,
            "aggregated": {
                **totals,
                "avg_ctr": round(avg_ctr, 2),
            },
        }

    def print_unified_report(self, days=28):
        """Print unified multi-tenant report to CLI."""
        report = self.generate_unified_report(days)
        agg = report["aggregated"]

        print("=" * 60)
        print(f"  MULTI-TENANT DASHBOARD — {report['generated_at']}")
        print(f"  Period: last {days} days | Tenants: {agg['tenants_count']}")
        print("=" * 60)
        print()
        print(f"  Total Articles (all tenants): {agg['total_articles']}")
        print(f"  Total Clicks:                 {agg['total_clicks']}")
        print(f"  Total Impressions:            {agg['total_impressions']}")
        print(f"  Avg CTR:                      {agg['avg_ctr']}%")
        print()

        for tenant_id, data in report["tenants"].items():
            if "error" in data:
                print(f"  [{tenant_id}] Error: {data['error']}")
                continue
            s = data.get("summary", {})
            print(f"  [{tenant_id}] Articles: {s.get('total_articles', 0)} | "
                  f"Clicks: {s.get('total_clicks', 0)} | "
                  f"Avg Pos: {s.get('avg_position', '-')}")

        print()
        print("=" * 60)
        return report
