"""Dashboard CLI — View article performance metrics."""
import argparse
import sys
from core.logger import setup_logger, get_logger
from core.dashboard.dashboard import PerformanceDashboard

setup_logger()
logger = get_logger("dashboard")


def main():
    parser = argparse.ArgumentParser(description="SEO Performance Dashboard")
    parser.add_argument('--tenant', type=str, default=None, help='Tenant ID (e.g., mjesus)')
    parser.add_argument('--days', type=int, default=28, help='Lookback period in days (default: 28)')
    parser.add_argument('--json', type=str, default=None, help='Save report to JSON file')
    parser.add_argument('--freshness', action='store_true', help='Run content freshness check')
    args = parser.parse_args()

    # Load tenant config
    wp = None
    gsc_url = ""
    sheets = None
    spreadsheet_id = ""

    if args.tenant:
        try:
            from core.tenant_config import TenantConfig
            from core.wordpress_client import WordPressClient
            from config.settings import load_wp_credentials

            tc = TenantConfig.load(args.tenant)
            site = tc.to_site_config()
            gsc_url = tc.wordpress_url

            try:
                wp_user, wp_pass = load_wp_credentials(site)
                wp = WordPressClient(tc.wordpress_url, wp_user, wp_pass)
            except Exception as e:
                logger.warning("WordPress unavailable: %s", e)

        except Exception as e:
            logger.error("Failed to load tenant '%s': %s", args.tenant, e)

    dashboard = PerformanceDashboard(
        wp_client=wp,
        gsc_property_url=gsc_url,
    )

    if args.freshness:
        from core.reoptimizer_v2 import ContentFreshnessEngine
        if not wp:
            logger.error("WordPress client required for freshness check. Use --tenant.")
            return 1
        engine = ContentFreshnessEngine(wp, {}, gsc_url)
        report = engine.run_freshness_check(days=args.days)
        print(f"\nDeclining: {report['declining_count']} | Page 2 Opportunities: {report['page2_opportunities']}")
        return 0

    if args.json:
        dashboard.save_json_report(args.json, days=args.days)
        print(f"Report saved to {args.json}")
    else:
        dashboard.print_cli_report(days=args.days)

    return 0


if __name__ == "__main__":
    sys.exit(main())
