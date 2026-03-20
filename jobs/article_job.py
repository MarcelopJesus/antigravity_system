"""Article generation job — processes one keyword for one tenant."""
import os
import re
import time
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase
from core.pipeline import ArticlePipeline, clean_orphan_placeholders
from core.agents.visual import VisualAgent
from core.agents.growth import GrowthAgent
from core.tenant_config import TenantConfig
from core.prompt_engine import PromptEngine
from core.kb_cache import KnowledgeBaseCache
from core.rate_limiter import RateLimiter
from core.circuit_breaker import CircuitBreaker
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient
from core.dry_run import save_dry_run_output
from core.logger import setup_logger, get_logger
from config.settings import load_wp_credentials

# Shared across jobs in the same worker process
_kb_cache = KnowledgeBaseCache(ttl=3600)
_rate_limiter = RateLimiter(rpm=15)
_circuit_breaker = CircuitBreaker(name="gemini", failure_threshold=5, cooldown=60)

setup_logger()
logger = get_logger("jobs.article")


def process_article(tenant_id, keyword, row_num=0, dry_run=False, priority="normal"):
    """Process a single article for a tenant.

    This is the main job function, designed to be enqueued by rq.

    Args:
        tenant_id: Company ID (e.g., "mjesus").
        keyword: Target keyword for the article.
        row_num: Row number in Google Sheets (0 if unknown).
        dry_run: If True, save locally instead of publishing.
        priority: Job priority (high, normal, low).

    Returns:
        Dict with job result: {status, tenant_id, keyword, seo_score, duration_ms, url, error}
    """
    start = time.time()
    result_data = {
        "status": "failed",
        "tenant_id": tenant_id,
        "keyword": keyword,
        "seo_score": 0,
        "duration_ms": 0,
        "url": "",
        "error": "",
    }

    try:
        # Load tenant config
        tc = TenantConfig.load(tenant_id)
        logger.info("[JOB] Processing: tenant=%s keyword='%s'", tenant_id, keyword)

        # Initialize components
        kb_path = tc.kb_path
        if not os.path.exists(kb_path):
            kb_path = f"config/companies/{tenant_id}/knowledge_base"

        llm = LLMClient(rate_limiter=_rate_limiter, circuit_breaker=_circuit_breaker)
        kb = KnowledgeBase(kb_path)
        prompt_engine = PromptEngine(tc)
        site = tc.to_site_config()

        agent_kwargs = {
            "prompt_engine": prompt_engine,
            "kb_cache": _kb_cache,
            "tenant_config": tc,
        }

        pipeline = ArticlePipeline(
            llm, kb,
            prompt_engine=prompt_engine,
            kb_cache=_kb_cache,
            tenant_config=tc,
        )

        # Get inventory for internal linking
        inventory = []
        sheets = None
        if not dry_run:
            try:
                sheets = SheetsClient('config/service_account.json')
                inventory = sheets.get_all_completed_articles(tc.spreadsheet_id)
            except Exception as e:
                logger.warning("[JOB] Could not load inventory: %s", e)

        # Run pipeline
        pipeline_result = pipeline.run(keyword, inventory, site_config=site)

        if not pipeline_result.success:
            raise ValueError(pipeline_result.error)

        final_content = pipeline_result.content
        final_title = pipeline_result.title

        if dry_run:
            final_content = clean_orphan_placeholders(final_content)
            pipeline_result.content = final_content
            html_path, json_path = save_dry_run_output(tenant_id, keyword, pipeline_result)
            logger.info("[JOB] DRY-RUN saved: %s", html_path)
            result_data["url"] = html_path
        else:
            # Visual (images)
            featured_media_id = 0
            if "visual" in tc.get_enabled_agents():
                try:
                    visual = VisualAgent(llm, kb, **agent_kwargs)
                    final_content, featured_media_id, _ = visual.process_images(
                        final_content, final_title, keyword, None, kb_path,
                        site_config=site, outline=pipeline_result.outline
                    )
                except Exception as e:
                    logger.warning("[JOB] Visual agent failed: %s", e)

            final_content = clean_orphan_placeholders(final_content)

            # Publish to WordPress
            wp_username, wp_password = load_wp_credentials(site)
            wp = WordPressClient(tc.wordpress_url, wp_username, wp_password)

            meta_desc = pipeline_result.meta_description
            if not meta_desc:
                clean = re.sub('<[^<]+?>', '', final_content)
                meta_desc = clean[:155] + "..."

            post = wp.create_post(
                title=final_title,
                content=final_content,
                featured_media_id=featured_media_id,
                status='publish',
                yoast_keyword=keyword,
                yoast_meta_desc=meta_desc,
                slug=pipeline_result.slug,
                excerpt=meta_desc,
                og_title=final_title,
                og_description=meta_desc,
            )
            result_data["url"] = post.get('link', '')
            logger.info("[JOB] Published: %s", result_data["url"])

            # Update Sheets
            if sheets and row_num > 0:
                sheets.update_row(tc.spreadsheet_id, row_num, result_data["url"], status="Done")

        # Growth suggestions
        if "growth" in tc.get_enabled_agents():
            try:
                growth = GrowthAgent(llm, kb, **agent_kwargs)
                growth_result = growth.execute({"title": final_title})
                if growth_result.success and sheets and not dry_run:
                    for topic in growth_result.content:
                        sheets.add_new_topic(tc.spreadsheet_id, topic)
            except Exception as e:
                logger.warning("[JOB] Growth agent failed: %s", e)

        result_data["status"] = "success"
        result_data["seo_score"] = pipeline_result.seo_score

    except Exception as e:
        result_data["error"] = str(e)[:200]
        logger.error("[JOB] Failed: tenant=%s keyword='%s' error=%s", tenant_id, keyword, e)

    result_data["duration_ms"] = round((time.time() - start) * 1000)
    logger.info("[JOB] Complete: %s in %dms", result_data["status"], result_data["duration_ms"])
    return result_data
