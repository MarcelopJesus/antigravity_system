"""Performance Dashboard — CLI and JSON output for article metrics."""
import json
import time
import os
from core.integrations.gsc_client import get_article_performance, get_keyword_performance
from core.logger import get_logger

logger = get_logger(__name__)


class PerformanceDashboard:
    """Aggregates metrics from GSC, WordPress, and pipeline data."""

    def __init__(self, wp_client=None, gsc_property_url=None, sheets_client=None,
                 spreadsheet_id=None):
        self.wp = wp_client
        self.gsc_url = gsc_property_url or os.getenv("GSC_PROPERTY_URL", "")
        self.sheets = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def generate_report(self, days=28):
        """Generate a comprehensive performance report.

        Returns:
            dict with all metrics.
        """
        report = {
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "period_days": days,
            "articles": self._get_article_metrics(),
            "gsc": self._get_gsc_metrics(days),
            "seo": self._get_seo_metrics(),
        }

        # Compute summary
        articles = report["articles"]
        gsc = report["gsc"]
        report["summary"] = {
            "total_articles": articles.get("total", 0),
            "avg_position": gsc.get("avg_position", 0),
            "total_clicks": gsc.get("total_clicks", 0),
            "total_impressions": gsc.get("total_impressions", 0),
            "avg_ctr": gsc.get("avg_ctr", 0),
            "page2_opportunities": len(gsc.get("page2_opportunities", [])),
        }

        return report

    def _get_article_metrics(self):
        """Get article counts from WordPress."""
        if not self.wp:
            return {"total": 0, "source": "unavailable"}

        try:
            posts = self.wp.get_posts()
            return {
                "total": len(posts),
                "source": "wordpress",
            }
        except Exception as e:
            logger.warning("Failed to get article metrics: %s", e)
            return {"total": 0, "source": "error"}

    def _get_gsc_metrics(self, days):
        """Get Google Search Console metrics."""
        if not self.gsc_url:
            return {"source": "unavailable", "reason": "GSC_PROPERTY_URL not configured"}

        try:
            pages = get_article_performance(self.gsc_url, days)
            keywords = get_keyword_performance(self.gsc_url, days)

            if not pages:
                return {"source": "no_data"}

            total_clicks = sum(p['clicks'] for p in pages)
            total_impressions = sum(p['impressions'] for p in pages)
            avg_position = sum(p['position'] for p in pages) / len(pages) if pages else 0
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

            # Top 5 by clicks
            top5 = sorted(pages, key=lambda x: x['clicks'], reverse=True)[:5]

            # Page 2 opportunities
            page2 = [p for p in pages if 11 <= p['position'] <= 20]
            page2.sort(key=lambda x: x['impressions'], reverse=True)

            return {
                "source": "gsc",
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "avg_position": round(avg_position, 1),
                "avg_ctr": round(avg_ctr, 2),
                "total_pages_tracked": len(pages),
                "total_keywords_tracked": len(keywords),
                "top5_by_clicks": top5,
                "page2_opportunities": page2[:10],
            }
        except Exception as e:
            logger.warning("Failed to get GSC metrics: %s", e)
            return {"source": "error", "error": str(e)}

    def _get_seo_metrics(self):
        """Get SEO score metrics from recent dry-run outputs."""
        output_dir = "output"
        if not os.path.exists(output_dir):
            return {"source": "no_output_dir"}

        scores = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(root, f), 'r') as fh:
                            data = json.load(fh)
                            score = data.get('seo_score', 0)
                            if score > 0:
                                scores.append(score)
                    except Exception:
                        continue

        if not scores:
            return {"source": "no_data"}

        return {
            "source": "output_files",
            "articles_scored": len(scores),
            "avg_score": round(sum(scores) / len(scores), 1),
            "min_score": min(scores),
            "max_score": max(scores),
        }

    def print_cli_report(self, days=28):
        """Print a formatted CLI report."""
        report = self.generate_report(days)
        s = report["summary"]

        print("=" * 60)
        print(f"  PERFORMANCE DASHBOARD — {report['generated_at']}")
        print(f"  Period: last {days} days")
        print("=" * 60)
        print()
        print(f"  Total Articles:      {s['total_articles']}")
        print(f"  Avg Google Position:  {s['avg_position']}")
        print(f"  Total Clicks:        {s['total_clicks']}")
        print(f"  Total Impressions:   {s['total_impressions']}")
        print(f"  Avg CTR:             {s['avg_ctr']}%")
        print(f"  Page 2 Opportunities: {s['page2_opportunities']}")
        print()

        # Top 5
        top5 = report["gsc"].get("top5_by_clicks", [])
        if top5:
            print("  TOP 5 ARTICLES (by clicks):")
            for i, item in enumerate(top5, 1):
                print(f"    {i}. {item['page'][-50:]}  — {item['clicks']} clicks, pos {item['position']}")
            print()

        # Page 2 opportunities
        opps = report["gsc"].get("page2_opportunities", [])
        if opps:
            print(f"  PAGE 2 OPPORTUNITIES ({len(opps)} articles):")
            for item in opps[:5]:
                print(f"    - {item['page'][-50:]}  — pos {item['position']}, {item['impressions']} impressions")
            print()

        # SEO scores
        seo = report["seo"]
        if seo.get("articles_scored"):
            print(f"  SEO SCORES (from dry-run outputs):")
            print(f"    Avg: {seo['avg_score']} | Min: {seo['min_score']} | Max: {seo['max_score']}")
            print()

        print("=" * 60)
        return report

    def save_json_report(self, filepath, days=28):
        """Save report as JSON file."""
        report = self.generate_report(days)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Dashboard report saved to %s", filepath)
        return report
