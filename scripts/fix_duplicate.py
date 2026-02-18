"""
Fix Duplicate Article — One-off script

Problem: "Hipnoterapia: O Guia Completo" exists in 2 URLs (keyword cannibalization).

KEEP (more complete, with TRI in title):
  https://mjesus.com.br/hipnoterapia-o-guia-completo-para-transformar-sua-vida-com-a-tri/

REDIRECT (duplicate to move to draft):
  https://mjesus.com.br/hipnoterapia-o-guia-completo-para-transformar-sua-vida/

Actions:
1. Change duplicate article status to 'draft' via WP REST API
2. Log redirect 301 instruction for WordPress admin

Usage:
  python scripts/fix_duplicate.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.wordpress_client import WordPressClient
from core.logger import setup_logger, get_logger
from config.settings import load_wp_credentials

setup_logger()
logger = get_logger("fix_duplicate")

# URLs
KEEP_URL = "hipnoterapia-o-guia-completo-para-transformar-sua-vida-com-a-tri"
DUPLICATE_SLUG = "hipnoterapia-o-guia-completo-para-transformar-sua-vida"


def find_post_by_slug(wp, slug):
    """Find a post by its slug."""
    import requests
    url = f"{wp.base_url}/wp-json/wp/v2/posts"
    params = {"slug": slug, "status": "publish"}
    r = requests.get(url, headers=wp.headers, params=params)
    if r.status_code == 200:
        posts = r.json()
        if posts:
            return posts[0]
    return None


def main():
    logger.info("=" * 60)
    logger.info("Fix Duplicate Article Script")
    logger.info("=" * 60)

    try:
        with open('config/sites.json', 'r') as f:
            sites = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load sites.json: %s", e)
        return 1

    site = sites[0]
    try:
        wp_username, wp_password = load_wp_credentials(site)
    except ValueError as e:
        logger.error("Credentials error: %s", e)
        return 1

    wp = WordPressClient(site['wordpress_url'], wp_username, wp_password)
    if not wp.verify_auth():
        logger.error("Cannot authenticate with WordPress.")
        return 1

    # Find the duplicate post
    logger.info("Looking for duplicate article with slug: '%s'", DUPLICATE_SLUG)
    duplicate = find_post_by_slug(wp, DUPLICATE_SLUG)

    if not duplicate:
        logger.info("Duplicate article not found (may already be fixed). Nothing to do.")
        return 0

    post_id = duplicate['id']
    post_title = duplicate.get('title', {}).get('rendered', 'Unknown')
    post_link = duplicate.get('link', '')

    logger.info("Found duplicate: ID=%d, Title='%s'", post_id, post_title)
    logger.info("Link: %s", post_link)

    # Move to draft (not delete)
    result = wp.update_post(post_id, {"status": "draft"})
    if result:
        logger.info("SUCCESS: Post %d moved to draft.", post_id)
    else:
        logger.error("FAILED to move post %d to draft.", post_id)
        return 1

    # Log redirect instruction
    logger.info("")
    logger.info("=" * 60)
    logger.info("REDIRECT 301 INSTRUCTION:")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Configure a 301 redirect in your WordPress admin:")
    logger.info("")
    logger.info("  FROM: /%s/", DUPLICATE_SLUG)
    logger.info("  TO:   /%s/", KEEP_URL)
    logger.info("")
    logger.info("Options to configure redirect:")
    logger.info("  1. Yoast Premium: SEO > Redirects > Add redirect")
    logger.info("  2. Redirection plugin: Tools > Redirection > Add new")
    logger.info("  3. .htaccess (if using Apache):")
    logger.info("     Redirect 301 /%s/ /%s/", DUPLICATE_SLUG, KEEP_URL)
    logger.info("")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
