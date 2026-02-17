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
from config.settings import load_wp_credentials

# Initialize logging before anything else
setup_logger()
logger = get_logger("main")


# Re-export validation helpers for backward compatibility (used by tests)
from core.pipeline import validate_analyst_output, validate_html_output


def main():
    logger.info("=" * 80)
    logger.info("SEO Orchestrator (Multi-Tenant) Starting...")
    logger.info("=" * 80)

    if not os.path.exists('config/service_account.json'):
        logger.error("'config/service_account.json' missing. Aborting.")
        return 1

    try:
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load sites.json: %s", e)
        return 1

    total_processed = 0
    total_success = 0
    total_errors = 0
    total_images_failed = 0

    for site in sites:
        company_id = site.get('company_id', 'default')
        site_name = site.get('site_name', 'Unknown')

        logger.info("=" * 80)
        logger.info("Processing Company: %s (ID: %s)", site_name, company_id)
        logger.info("=" * 80)

        company_processed = 0
        company_success = 0
        company_errors = 0
        company_images_failed = 0

        kb_path = f"config/companies/{company_id}/knowledge_base"
        try:
            llm = LLMClient()
            kb = KnowledgeBase(kb_path)
            pipeline = ArticlePipeline(llm, kb)
            visual = VisualAgent(llm, kb)
            growth = GrowthAgent(llm, kb)
            logger.info("Pipeline initialized for '%s' with KB path: %s", company_id, kb_path)
        except Exception as e:
            logger.error("Error initializing pipeline for '%s': %s", company_id, e)
            continue

        try:
            sheets = SheetsClient('config/service_account.json')
            pending_keywords = sheets.get_pending_rows(site['spreadsheet_id'])
            logger.info("Fetching Article Inventory for Link Building...")
            inventory = sheets.get_all_completed_articles(site['spreadsheet_id'])
            logger.info("Found %d existing articles for potential linking.", len(inventory))
            logger.info("Found %d pending keywords to write.", len(pending_keywords))
        except Exception as e:
            logger.error("Error accessing sheets for '%s': %s", company_id, e)
            continue

        try:
            wp_username, wp_password = load_wp_credentials(site)
        except ValueError as e:
            logger.error("Credentials error for '%s': %s", company_id, e)
            continue

        wp = WordPressClient(site['wordpress_url'], wp_username, wp_password)
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
                try:
                    sheets.update_row(site['spreadsheet_id'], row_num, "", status=f"Error: {validation_error[:50]}")
                except Exception:
                    pass
                continue
            seen_keywords.add(keyword.strip().lower())

            try:
                # Run the 4-agent article pipeline
                result = pipeline.run(keyword, inventory)

                if not result.success:
                    raise ValueError(result.error)

                final_title = result.title
                final_content = result.content
                outline_json = result.outline

                # STEP 5: VISUAL (Images)
                final_content, featured_media_id, img_failures = visual.process_images(
                    final_content, final_title, keyword, wp, kb_path
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
                    yoast_meta_desc=meta_desc
                )
                link = post.get('link')
                logger.info("  POSTED SUCCESSFULLY! Link: %s", link)

                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")
                company_success += 1

                # STEP 6: GROWTH HACKER
                logger.info("  6. Growth Hacker Agent: Suggesting new topics...")
                try:
                    growth_result = growth.execute({"title": final_title})
                    if growth_result.success:
                        for topic in growth_result.content:
                            logger.info("     New Idea: %s", topic)
                            sheets.add_new_topic(site['spreadsheet_id'], topic)
                except Exception as gh_err:
                    logger.warning("  Growth Hacker failed (non-critical): %s", gh_err)

            except Exception as e:
                company_errors += 1
                logger.error("FAILED keyword '%s' (row %d): %s", keyword, row_num, e, exc_info=True)
                try:
                    error_msg = str(e)[:80]
                    sheets.update_row(site['spreadsheet_id'], row_num, "", status=f"Error: {error_msg}")
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
    logger.info("=" * 80)

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
