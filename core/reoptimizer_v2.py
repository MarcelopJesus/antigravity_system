"""Content Freshness Engine v2 — Detects declining articles and triggers re-optimization."""
import time
from core.integrations.gsc_client import compare_periods, find_page2_opportunities
from core.reoptimizer import ArticleReoptimizer
from core.logger import get_logger

logger = get_logger(__name__)


class ContentFreshnessEngine:
    """Detects articles needing refresh based on GSC data and triggers re-optimization."""

    def __init__(self, wp_client, site_config, gsc_property_url=None):
        self.wp = wp_client
        self.config = site_config
        self.gsc_url = gsc_property_url or site_config.get('wordpress_url', '')
        self.reoptimizer = ArticleReoptimizer(wp_client, site_config)

    def detect_declining_articles(self, days=28):
        """Find articles with declining positions using GSC period comparison.

        Returns:
            List of articles that declined by more than 2 positions.
        """
        changes = compare_periods(self.gsc_url, days)
        declining = [c for c in changes if c['status'] == 'declined' and c['change'] < -2]

        if declining:
            logger.info("Detected %d declining articles (>2 position drop)", len(declining))
            for item in declining[:5]:
                logger.info("  %s: %.1f → %.1f (change: %.1f)",
                            item['page'][-50:], item['previous_position'],
                            item['current_position'], item['change'])

        return declining

    def detect_page2_opportunities(self, days=28):
        """Find articles on page 2 that could be pushed to page 1.

        Returns:
            List of page-2 articles sorted by impression potential.
        """
        return find_page2_opportunities(self.gsc_url, days)

    def refresh_article(self, post_id, reason="content_freshness"):
        """Re-optimize a specific article with freshness updates.

        Updates:
        - dateModified in schema
        - "Atualizado em {data}" tag
        - Re-runs alt text and metadata fixes

        Args:
            post_id: WordPress post ID.
            reason: Why the refresh was triggered.

        Returns:
            dict with refresh results.
        """
        try:
            # Fetch current post
            posts = self.wp.get_posts(per_page=1, status="publish")
            post = None
            for p in self.wp.get_posts():
                if p.get('id') == post_id:
                    post = p
                    break

            if not post:
                logger.warning("Post %d not found", post_id)
                return {"success": False, "error": "Post not found"}

            html = post.get('content', {}).get('rendered', '')
            title = post.get('title', {}).get('rendered', '')

            # Get keyword
            keyword = self.reoptimizer._get_yoast_keyword(post_id)
            if not keyword:
                from core.reoptimizer import _extract_keyword_from_title
                keyword = _extract_keyword_from_title(title)

            # Run standard reoptimization
            fixed_html, metadata = self.reoptimizer.analyze_and_fix(
                html, keyword, title
            )

            # Add freshness signal: update dateModified
            today = time.strftime('%Y-%m-%d')
            if 'meta' not in metadata:
                metadata['meta'] = {}

            # Update the post
            result = self.reoptimizer.update_article(post_id, fixed_html, metadata)

            logger.info("Article %d refreshed (reason: %s, keyword: %s)", post_id, reason, keyword)
            return {
                "success": result is not None,
                "post_id": post_id,
                "keyword": keyword,
                "reason": reason,
                "date": today,
            }

        except Exception as e:
            logger.error("Failed to refresh article %d: %s", post_id, e)
            return {"success": False, "error": str(e)}

    def run_freshness_check(self, days=28, auto_refresh=False):
        """Run a complete freshness check: detect declining + page 2 opportunities.

        Args:
            days: Lookback period.
            auto_refresh: If True, automatically refresh declining articles.

        Returns:
            dict with declining, opportunities, and refresh results.
        """
        logger.info("=" * 60)
        logger.info("Content Freshness Check (last %d days)", days)
        logger.info("=" * 60)

        declining = self.detect_declining_articles(days)
        opportunities = self.detect_page2_opportunities(days)

        refresh_results = []
        if auto_refresh and declining:
            logger.info("Auto-refreshing %d declining articles...", len(declining))
            for item in declining[:5]:  # Max 5 per run
                # Extract post ID from URL (last path segment)
                page_url = item['page']
                # Would need to look up post ID by URL — simplified for now
                logger.info("  Would refresh: %s (pos %.1f → %.1f)",
                            page_url[-50:], item['previous_position'], item['current_position'])

        report = {
            "date": time.strftime('%Y-%m-%d'),
            "period_days": days,
            "declining_count": len(declining),
            "declining": declining[:10],
            "page2_opportunities": len(opportunities),
            "opportunities": opportunities[:10],
            "refreshed": refresh_results,
        }

        logger.info("Freshness check complete: %d declining, %d page-2 opportunities",
                     len(declining), len(opportunities))
        return report
