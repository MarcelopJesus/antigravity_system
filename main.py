import json
import os
import re
import sys
import base64
from core.gemini_brain import GeminiBrain
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient
from core.logger import setup_logger, get_logger
from config.settings import load_wp_credentials

# Initialize logging before anything else
setup_logger()
logger = get_logger("main")


# =========================================================================
# VALIDATION HELPERS (Story 1.5)
# =========================================================================

def validate_keyword(keyword, seen_keywords):
    """Validates a keyword before processing."""
    if not keyword or not keyword.strip():
        return False, "Keyword is empty"
    if len(keyword) > 200:
        return False, f"Keyword too long ({len(keyword)} chars, max 200)"
    if keyword.strip().lower() in seen_keywords:
        return False, f"Duplicate keyword in this batch: '{keyword}'"
    return True, ""


def validate_analyst_output(outline_json):
    """Validates the analyst agent output (JSON structure)."""
    if not isinstance(outline_json, dict):
        return False, "Analyst output is not a valid JSON object"
    required_fields = ['title', 'sections']
    missing = [f for f in required_fields if f not in outline_json]
    if missing:
        return False, f"Analyst output missing required fields: {missing}"
    if not outline_json.get('title', '').strip():
        return False, "Analyst output has empty title"
    return True, ""


def validate_html_output(html, agent_name, min_ratio=0.0, reference_len=0):
    """Validates HTML output from writer/humanizer/editor agents."""
    if not html or not html.strip():
        return False, f"{agent_name} returned empty output"
    if len(html.strip()) < 100:
        return False, f"{agent_name} output too short ({len(html)} chars)"
    # Check for residual markdown code blocks
    if html.strip().startswith("```"):
        return False, f"{agent_name} output starts with markdown code block"
    # Check minimum ratio (for humanizer — shouldn't delete too much content)
    if min_ratio > 0 and reference_len > 0:
        ratio = len(html) / reference_len
        if ratio < min_ratio:
            return False, f"{agent_name} output is only {ratio:.0%} of input (min {min_ratio:.0%})"
    return True, ""


def clean_orphan_placeholders(html):
    """Removes any remaining IMG_PLACEHOLDER tags from final HTML."""
    return html.replace("<!-- IMG_PLACEHOLDER -->", "")


# =========================================================================
# MAIN PIPELINE
# =========================================================================

def main():
    logger.info("=" * 80)
    logger.info("SEO Orchestrator (Multi-Tenant) Starting...")
    logger.info("=" * 80)

    # Check for service account
    if not os.path.exists('config/service_account.json'):
        logger.error("'config/service_account.json' missing. Aborting.")
        return 1

    # Load sites configuration
    try:
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load sites.json: %s", e)
        return 1

    # Global counters for final report
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

        # Per-company counters
        company_processed = 0
        company_success = 0
        company_errors = 0
        company_images_failed = 0

        # Initialize Brain with company-specific knowledge base
        kb_path = f"config/companies/{company_id}/knowledge_base"
        try:
            brain = GeminiBrain(knowledge_base_path=kb_path)
            logger.info("Brain initialized for '%s' with KB path: %s", company_id, kb_path)
        except Exception as e:
            logger.error("Error initializing Gemini for '%s': %s", company_id, e)
            continue

        # Init Sheets
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

        # Init WordPress (credentials from .env or legacy sites.json)
        try:
            wp_username, wp_password = load_wp_credentials(site)
        except ValueError as e:
            logger.error("Credentials error for '%s': %s", company_id, e)
            continue

        wp = WordPressClient(
            site['wordpress_url'],
            wp_username,
            wp_password
        )
        if not wp.verify_auth():
            logger.error("Cannot authenticate with WordPress for '%s'. Skipping.", company_id)
            continue

        # Track seen keywords to detect duplicates in batch
        seen_keywords = set()

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            company_processed += 1

            logger.info("-" * 60)
            logger.info("Working on Keyword: '%s' (row %d)", keyword, row_num)

            # --- Input Validation (Story 1.5) ---
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
                # ---------------------------------------------------------
                # STEP 1: ANALYST (Plan & Structure)
                # ---------------------------------------------------------
                logger.info("  1. Analyst Agent: Creating Strategic Outline...")
                outline_json = brain.analyze_and_plan(keyword, inventory)

                # Validate analyst output
                is_valid, err = validate_analyst_output(outline_json)
                if not is_valid:
                    raise ValueError(f"Analyst validation failed: {err}")

                final_title = outline_json.get('title', keyword.title())
                logger.info("     Title: %s", final_title)

                # ---------------------------------------------------------
                # STEP 2: WRITER (Drafting)
                # ---------------------------------------------------------
                logger.info("  2. Senior Writer Agent: Writing Content...")
                draft_html = brain.write_article_body(outline_json)

                is_valid, err = validate_html_output(draft_html, "Writer")
                if not is_valid:
                    raise ValueError(f"Writer validation failed: {err}")

                # ---------------------------------------------------------
                # STEP 3: HUMANIZADOR TRI
                # ---------------------------------------------------------
                logger.info("  3. Humanizer Agent: Injecting TRI Voice...")
                humanized_html = brain.humanize_with_tri_voice(draft_html)

                is_valid, err = validate_html_output(
                    humanized_html, "Humanizer",
                    min_ratio=0.5, reference_len=len(draft_html)
                )
                if not is_valid:
                    raise ValueError(f"Humanizer validation failed: {err}")

                # ---------------------------------------------------------
                # STEP 4: EDITOR
                # ---------------------------------------------------------
                logger.info("  4. Editor Agent: Polishing & SEO Check...")
                final_content = brain.edit_and_refine(humanized_html)

                is_valid, err = validate_html_output(final_content, "Editor")
                if not is_valid:
                    raise ValueError(f"Editor validation failed: {err}")

                # ---------------------------------------------------------
                # STEP 5: VISUAL (Images)
                # ---------------------------------------------------------
                logger.info("  5. Visual Agent: Generating Editorial Images...")
                prompts_str = brain.generate_image_prompts(final_content)

                prompts_list = [p.strip() for p in prompts_str.split('|||') if p.strip()]

                featured_media_id = None
                slug = keyword.replace(" ", "-").lower()[:30]

                # ---- IMAGE 1: AI-Generated Cover ----
                if len(prompts_list) >= 1:
                    logger.info("     Image 1 (Cover): Generating AI editorial image...")
                    try:
                        b64_image = brain.generate_final_images(prompts_list[0])
                        if b64_image:
                            image_data = base64.b64decode(b64_image)
                            filename = f"{slug}-capa.png"
                            media_id, media_url = wp.upload_media(image_data, filename)
                            featured_media_id = media_id
                            logger.info("     Featured Image Set (ID: %s)", media_id)
                        else:
                            logger.warning("     Cover image generation returned empty. Publishing without featured image.")
                            company_images_failed += 1
                    except Exception as img_err:
                        logger.warning("     Cover image failed: %s. Publishing without featured image.", img_err)
                        company_images_failed += 1

                # ---- IMAGE 2: Real Author Photo ----
                logger.info("     Image 2 (Author): Loading real author photo...")
                try:
                    author_photo_data, author_photo_filename = brain.get_real_author_photo()

                    if author_photo_data:
                        ext = author_photo_filename.split('.')[-1].lower()
                        upload_filename = f"{slug}-terapeuta.{ext}"
                        media_id, media_url = wp.upload_media(author_photo_data, upload_filename)

                        if media_url:
                            author_img_html = (
                                f"<figure class='wp-block-image aligncenter size-large'>"
                                f"<img src='{media_url}' alt='Marcelo Jesus - Terapeuta TRI em Moema, São Paulo'/>"
                                f"<figcaption>Marcelo Jesus — Terapeuta especialista em TRI | Consultório em Moema, SP</figcaption>"
                                f"</figure>"
                            )

                            if "<!-- IMG_PLACEHOLDER -->" in final_content:
                                final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", author_img_html, 1)
                                logger.info("     Author photo injected into placeholder.")
                            else:
                                h2_match = re.search(r'(</h2>)', final_content)
                                if h2_match:
                                    insert_pos = h2_match.end()
                                    final_content = final_content[:insert_pos] + "\n" + author_img_html + "\n" + final_content[insert_pos:]
                                    logger.info("     Author photo inserted after first H2.")
                                else:
                                    final_content += "\n" + author_img_html
                                    logger.info("     Author photo appended to end.")
                    else:
                        logger.warning("     No author photos found. Skipping Image 2.")
                        company_images_failed += 1
                except Exception as img_err:
                    logger.warning("     Author photo failed: %s. Continuing without it.", img_err)
                    company_images_failed += 1

                # ---- IMAGE 3: AI-Generated Final ----
                if len(prompts_list) >= 2:
                    logger.info("     Image 3 (Final): Generating AI editorial image...")
                    try:
                        b64_image = brain.generate_final_images(prompts_list[1])
                        if b64_image:
                            image_data = base64.b64decode(b64_image)
                            filename = f"{slug}-final.png"
                            media_id, media_url = wp.upload_media(image_data, filename)

                            final_img_html = f"<figure class='wp-block-image'><img src='{media_url}' alt='{final_title}'/></figure>"

                            if "<!-- IMG_PLACEHOLDER -->" in final_content:
                                final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", final_img_html, 1)
                                logger.info("     Final image injected into placeholder.")
                            else:
                                if '<div class="cta-box">' in final_content:
                                    final_content = final_content.replace(
                                        '<div class="cta-box">',
                                        final_img_html + '\n<div class="cta-box">'
                                    )
                                    logger.info("     Final image inserted before CTA.")
                                else:
                                    final_content += "\n" + final_img_html
                                    logger.info("     Final image appended to end.")
                        else:
                            logger.warning("     Final image generation returned empty. Publishing without it.")
                            company_images_failed += 1
                    except Exception as img_err:
                        logger.warning("     Final image failed: %s. Publishing without it.", img_err)
                        company_images_failed += 1

                # Clean orphan placeholders before publishing (Story 1.6)
                final_content = clean_orphan_placeholders(final_content)

                # ---------------------------------------------------------
                # POST TO WORDPRESS
                # ---------------------------------------------------------
                logger.info("  Publishing to WordPress...")

                meta_desc = outline_json.get('meta_description', "")
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

                # Update Sheet
                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")
                company_success += 1

                # ---------------------------------------------------------
                # STEP 6: GROWTH HACKER
                # ---------------------------------------------------------
                logger.info("  6. Growth Hacker Agent: Suggesting new topics...")
                try:
                    new_topics = brain.identify_new_topics(final_title, final_content)
                    for topic in new_topics:
                        logger.info("     New Idea: %s", topic)
                        sheets.add_new_topic(site['spreadsheet_id'], topic)
                except Exception as gh_err:
                    logger.warning("  Growth Hacker failed (non-critical): %s", gh_err)

            except Exception as e:
                company_errors += 1
                logger.error("FAILED keyword '%s' (row %d): %s", keyword, row_num, e, exc_info=True)
                # Update sheet with error status
                try:
                    error_msg = str(e)[:80]
                    sheets.update_row(site['spreadsheet_id'], row_num, "", status=f"Error: {error_msg}")
                except Exception as sheet_err:
                    logger.error("Could not update sheet with error status: %s", sheet_err)

        # Per-company summary
        logger.info("=" * 60)
        logger.info("COMPANY SUMMARY: %s", site_name)
        logger.info("  Processed: %d | Success: %d | Errors: %d | Images Failed: %d",
                     company_processed, company_success, company_errors, company_images_failed)
        logger.info("=" * 60)

        total_processed += company_processed
        total_success += company_success
        total_errors += company_errors
        total_images_failed += company_images_failed

    # Final consolidated report
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
