import argparse
import json
import os
import re
import sys
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase
from core.pipeline import ArticlePipeline, validate_keyword, clean_orphan_placeholders
from core.agents.visual import VisualAgent
from core.agents.growth import GrowthAgent
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient
from core.logger import setup_logger, get_logger
from core.dry_run import load_keywords_from_file, save_dry_run_output
from config.settings import load_wp_credentials
from core.tenant_config import TenantConfig
from core.prompt_engine import PromptEngine
from core.kb_cache import KnowledgeBaseCache
from core.rate_limiter import RateLimiter
from core.circuit_breaker import CircuitBreaker

# Initialize logging before anything else
setup_logger()
logger = get_logger("main")


# Re-export validation helpers for backward compatibility (used by tests)
from core.pipeline import validate_analyst_output, validate_html_output


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="SEO Orchestrator — Multi-Tenant Article Pipeline"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Run pipeline but save output locally instead of publishing to WordPress/Sheets'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        default=None,
        help='Path to a JSON file with keywords (used with --dry-run to skip Sheets read)'
    )
    parser.add_argument(
        '--reoptimize',
        action='store_true',
        default=False,
        help='Re-optimize existing WordPress articles (fix alt text, inject schema, update metadata)'
    )
    return parser.parse_args(argv)


def main(dry_run=False, keywords_file=None):
    logger.info("=" * 80)
    if dry_run:
        logger.info("SEO Orchestrator (Multi-Tenant) Starting in DRY-RUN mode...")
    else:
        logger.info("SEO Orchestrator (Multi-Tenant) Starting...")
    logger.info("=" * 80)

    if not dry_run and not os.path.exists('config/service_account.json'):
        logger.error("'config/service_account.json' missing. Aborting.")
        return 1

    if dry_run and keywords_file and not os.path.exists(keywords_file):
        logger.error("Keywords file '%s' not found. Aborting.", keywords_file)
        return 1

    # --- Load tenants: try new config/tenants/ first, fallback to sites.json ---
    tenant_configs = _load_tenant_configs()
    if not tenant_configs:
        logger.error("No tenants found. Check config/tenants/ or config/sites.json.")
        return 1

    # Shared infrastructure
    rate_limiter = RateLimiter(rpm=15)
    circuit_breaker = CircuitBreaker(name="gemini", failure_threshold=5, cooldown=60)
    kb_cache = KnowledgeBaseCache(ttl=3600)

    total_processed = 0
    total_success = 0
    total_errors = 0
    total_images_failed = 0

    for tc in tenant_configs:
        company_id = tc.company_id
        site_name = tc.site_name

        logger.info("=" * 80)
        logger.info("Processing Company: %s (ID: %s)", site_name, company_id)
        logger.info("=" * 80)

        company_processed = 0
        company_success = 0
        company_errors = 0
        company_images_failed = 0

        kb_path = tc.kb_path
        # Fallback KB path for legacy structure
        if not os.path.exists(kb_path):
            kb_path = f"config/companies/{company_id}/knowledge_base"

        try:
            llm = LLMClient(rate_limiter=rate_limiter, circuit_breaker=circuit_breaker)
            kb = KnowledgeBase(kb_path)
            prompt_engine = PromptEngine(tc)
            pipeline = ArticlePipeline(
                llm, kb,
                prompt_engine=prompt_engine,
                kb_cache=kb_cache,
                tenant_config=tc,
            )
            agent_kwargs = {
                "prompt_engine": prompt_engine,
                "kb_cache": kb_cache,
                "tenant_config": tc,
            }
            if not dry_run and "visual" in tc.get_enabled_agents():
                visual = VisualAgent(llm, kb, **agent_kwargs)
            else:
                visual = None
            if "growth" in tc.get_enabled_agents():
                growth = GrowthAgent(llm, kb, **agent_kwargs)
            else:
                growth = None
            logger.info("Pipeline initialized for '%s' with KB path: %s", company_id, kb_path)
        except Exception as e:
            logger.error("Error initializing pipeline for '%s': %s", company_id, e)
            continue

        # Convert TenantConfig to site_config dict for backward compat
        site = tc.to_site_config()

        # --- Keywords source ---
        if dry_run and keywords_file:
            try:
                pending_keywords = load_keywords_from_file(keywords_file)
                inventory = []
                logger.info("[DRY-RUN] Loaded %d keywords from %s", len(pending_keywords), keywords_file)
            except Exception as e:
                logger.error("Error loading keywords file '%s': %s", keywords_file, e)
                continue
        else:
            if not dry_run and not os.path.exists('config/service_account.json'):
                logger.error("'config/service_account.json' missing. Skipping '%s'.", company_id)
                continue
            try:
                sheets = SheetsClient('config/service_account.json')
                pending_keywords = sheets.get_pending_rows(tc.spreadsheet_id)
                logger.info("Fetching Article Inventory for Link Building...")
                inventory = sheets.get_all_completed_articles(tc.spreadsheet_id)
                logger.info("Found %d existing articles for potential linking.", len(inventory))
                logger.info("Found %d pending keywords to write.", len(pending_keywords))
            except Exception as e:
                logger.error("Error accessing sheets for '%s': %s", company_id, e)
                continue

        # --- WordPress setup (skip in dry-run) ---
        wp = None
        if not dry_run:
            try:
                wp_username, wp_password = load_wp_credentials(site)
            except ValueError as e:
                logger.error("Credentials error for '%s': %s", company_id, e)
                continue

            wp = WordPressClient(tc.wordpress_url, wp_username, wp_password)
            if not wp.verify_auth():
                logger.error("Cannot authenticate with WordPress for '%s'. Skipping.", company_id)
                continue

        seen_keywords = set()

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            company_processed += 1

            logger.info("-" * 60)
            logger.info("Working on Keyword: '%s' (row %d)", keyword, row_num)

            is_valid, validation_error = validate_keyword(keyword, seen_keywords)
            if not is_valid:
                logger.warning("Skipping invalid keyword (row %d): %s", row_num, validation_error)
                company_errors += 1
                if not dry_run:
                    try:
                        sheets.update_row(tc.spreadsheet_id, row_num, "", status=f"Error: {validation_error[:50]}")
                    except Exception:
                        pass
                continue
            seen_keywords.add(keyword.strip().lower())

            try:
                # Run the 4-agent article pipeline
                result = pipeline.run(keyword, inventory, site_config=site)

                if not result.success:
                    if result.seo_grade == "D":
                        logger.error("  SEO Gate blocked publication (grade D, score %d)", result.seo_score)
                    raise ValueError(result.error)

                final_title = result.title
                final_content = result.content

                if dry_run:
                    # DRY-RUN: skip images, save locally
                    final_content = clean_orphan_placeholders(final_content)
                    result.content = final_content
                    html_path, json_path = save_dry_run_output(company_id, keyword, result)
                    logger.info("  [DRY-RUN] Article saved to %s", html_path)
                    company_success += 1

                    # Log priority keywords for missing internal links
                    if result.missing_link_keywords:
                        for priority_kw in result.missing_link_keywords:
                            logger.info("  [DRY-RUN] 🔗 PRIORITY keyword for planilha: '%s'", priority_kw)
                else:
                    # PRODUCTION: images + WordPress + Sheets
                    # STEP 5: VISUAL (Images) — only if enabled
                    featured_media_id = 0
                    if visual:
                        final_content, featured_media_id, img_failures = visual.process_images(
                            final_content, final_title, keyword, wp, kb_path,
                            site_config=site, outline=result.outline
                        )
                        company_images_failed += img_failures

                    # Clean orphan placeholders
                    final_content = clean_orphan_placeholders(final_content)

                    # POST TO WORDPRESS
                    logger.info("  Publishing to WordPress...")
                    meta_desc = result.meta_description
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
                        slug=result.slug,
                        excerpt=result.excerpt,
                        og_title=final_title,
                        og_description=meta_desc,
                    )
                    link = post.get('link')
                    logger.info("  POSTED SUCCESSFULLY! Link: %s", link)

                    sheets.update_row(tc.spreadsheet_id, row_num, link, status="Done")
                    company_success += 1

                    # Add priority keywords for missing internal links
                    if result.missing_link_keywords:
                        for priority_kw in result.missing_link_keywords:
                            sheets.add_priority_keyword(
                                tc.spreadsheet_id, priority_kw, source_article=final_title
                            )

                # GROWTH HACKER (both modes — but skip Sheets write in dry-run)
                if growth:
                    logger.info("  6. Growth Hacker Agent: Suggesting new topics...")
                    try:
                        growth_result = growth.execute({"title": final_title})
                        if growth_result.success:
                            for topic in growth_result.content:
                                logger.info("     New Idea: %s", topic)
                                if not dry_run:
                                    sheets.add_new_topic(tc.spreadsheet_id, topic)
                                else:
                                    logger.info("     [DRY-RUN] Would add topic to sheet: %s", topic)
                    except Exception as gh_err:
                        logger.warning("  Growth Hacker failed (non-critical): %s", gh_err)

            except Exception as e:
                company_errors += 1
                logger.error("FAILED keyword '%s' (row %d): %s", keyword, row_num, e, exc_info=True)
                if not dry_run:
                    try:
                        error_msg = str(e)[:80]
                        sheets.update_row(tc.spreadsheet_id, row_num, "", status=f"Error: {error_msg}")
                    except Exception as sheet_err:
                        logger.error("Could not update sheet with error status: %s", sheet_err)

        logger.info("=" * 60)
        logger.info("COMPANY SUMMARY: %s", site_name)
        logger.info("  Processed: %d | Success: %d | Errors: %d | Images Failed: %d",
                     company_processed, company_success, company_errors, company_images_failed)
        logger.info("=" * 60)

        total_processed += company_processed
        total_success += company_success
        total_errors += company_errors
        total_images_failed += company_images_failed

    logger.info("=" * 80)
    logger.info("FINAL REPORT")
    logger.info("  Total Processed: %d", total_processed)
    logger.info("  Total Success:   %d", total_success)
    logger.info("  Total Errors:    %d", total_errors)
    logger.info("  Images Failed:   %d", total_images_failed)
    logger.info("  KB Cache: %s", kb_cache.stats)
    logger.info("  Rate Limiter: %s", rate_limiter.stats)
    logger.info("=" * 80)

    return 1 if total_errors > 0 else 0


def _load_tenant_configs():
    """Load tenant configs from config/tenants/ or fallback to sites.json.

    Returns:
        List of TenantConfig instances.
    """
    # Try new tenant config structure first
    tenants = TenantConfig.list_all()
    if tenants:
        configs = []
        for tenant_id in tenants:
            try:
                tc = TenantConfig.load(tenant_id)
                configs.append(tc)
                logger.info("Loaded tenant: %s", tenant_id)
            except Exception as e:
                logger.error("Error loading tenant '%s': %s", tenant_id, e)
        if configs:
            return configs

    # Fallback to sites.json
    logger.info("No tenants in config/tenants/. Falling back to sites.json...")
    try:
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
        return [TenantConfig.from_site_config(site) for site in sites]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load sites.json: %s", e)
        return []


def reoptimize():
    """Re-optimize all existing WordPress articles."""
    from core.reoptimizer import ArticleReoptimizer

    logger.info("=" * 80)
    logger.info("SEO Re-Optimizer Starting...")
    logger.info("=" * 80)

    try:
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load sites.json: %s", e)
        return 1

    for site in sites:
        company_id = site.get('company_id', 'default')
        site_name = site.get('site_name', 'Unknown')

        logger.info("Re-optimizing site: %s (%s)", site_name, company_id)

        try:
            wp_username, wp_password = load_wp_credentials(site)
        except ValueError as e:
            logger.error("Credentials error for '%s': %s", company_id, e)
            continue

        wp = WordPressClient(site['wordpress_url'], wp_username, wp_password)
        if not wp.verify_auth():
            logger.error("Cannot authenticate with WordPress for '%s'. Skipping.", company_id)
            continue

        optimizer = ArticleReoptimizer(wp, site)
        results = optimizer.reoptimize_all()

        success_count = sum(1 for r in results if r['success'])
        logger.info("Site '%s': %d/%d posts re-optimized", site_name, success_count, len(results))

    logger.info("=" * 80)
    logger.info("Re-optimization complete!")
    logger.info("=" * 80)
    return 0


if __name__ == "__main__":
    args = parse_args()
    if args.reoptimize:
        exit_code = reoptimize()
    else:
        exit_code = main(dry_run=args.dry_run, keywords_file=args.keywords)
    sys.exit(exit_code)
