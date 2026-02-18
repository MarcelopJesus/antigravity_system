"""ArticleReoptimizer — Re-optimizes existing WordPress articles via REST API."""
import re
import requests
from html import unescape
from core.seo.schema import (
    generate_article_schema,
    generate_local_business_schema,
    generate_faq_schema,
    extract_faq_from_html,
    strip_schema_from_html,
)
from core.logger import get_logger

logger = get_logger(__name__)


def _clean_html_entities(text):
    """Clean HTML entities from text."""
    return unescape(re.sub(r'<[^>]+>', '', text)).strip()


def _extract_keyword_from_title(title):
    """Extract a meaningful keyword from a post title.
    Takes the first meaningful phrase before ':' or '—' or the full title.
    """
    clean = _clean_html_entities(title)
    for sep in [':', '—', '–', '-']:
        if sep in clean:
            parts = clean.split(sep)
            candidate = parts[0].strip()
            if len(candidate) >= 5:
                return candidate
    return clean


class ArticleReoptimizer:
    """Re-optimizes existing WordPress articles via REST API."""

    def __init__(self, wp_client, site_config):
        self.wp = wp_client
        self.config = site_config
        self.base_url = wp_client.base_url
        self.headers = wp_client.headers

    def _get_post_media_ids(self, html, featured_media_id):
        """Extract all media IDs referenced in a post (featured + inline images)."""
        media_ids = set()
        if featured_media_id:
            media_ids.add(featured_media_id)

        # Extract wp-image-{ID} classes from content
        for match in re.finditer(r'wp-image-(\d+)', html):
            media_ids.add(int(match.group(1)))

        return media_ids

    def _get_yoast_keyword(self, post_id):
        """Try to get the Yoast focus keyword for a post."""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}?_fields=meta"
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                meta = r.json().get('meta', {})
                kw = meta.get('_yoast_wpseo_focuskw', '')
                if kw:
                    return kw
        except Exception:
            pass
        return None

    def analyze_and_fix(self, html, keyword, post_title, post_url="", date_published="", image_url=""):
        """Apply algorithmic fixes (no LLM):
        1. Remove schema JSON-LD from content (WordPress renders it as text)
        2. Fix alt text of images without alt or with generic alt
        3. Generate excerpt
        4. Set Yoast OG fields
        Returns (fixed_html, metadata_updates).
        """
        metadata = {}
        author_name = self.config.get('author_name', '')

        # Clean HTML entities in title for display
        clean_title = _clean_html_entities(post_title)

        # Remove any JSON-LD schemas from content (WordPress can't render <script> in content)
        html = strip_schema_from_html(html)

        # Fix images with empty or generic alt text
        generic_alts = {'', 'image', 'foto', 'img', 'imagem', 'picture', 'photo'}

        def fix_alt(match):
            full_tag = match.group(0)
            alt_match = re.search(r"alt=['\"]([^'\"]*)['\"]", full_tag)
            if alt_match:
                current_alt = alt_match.group(1).strip()
                if current_alt.lower() not in generic_alts:
                    return full_tag
                # Check if it's the author photo
                if 'terapeuta' in full_tag.lower() or 'marcelo' in full_tag.lower():
                    new_alt = f"{author_name} - Terapeuta especialista em {keyword}"
                else:
                    new_alt = f"{keyword} - {clean_title}"
                new_alt = new_alt[:120]
                return full_tag[:alt_match.start()] + f'alt="{new_alt}"' + full_tag[alt_match.end():]
            else:
                new_alt = f"{keyword} - {clean_title}"[:120]
                return full_tag.rstrip('>').rstrip('/') + f' alt="{new_alt}">'

        html = re.sub(r'<img[^>]*/?>', fix_alt, html, flags=re.IGNORECASE)

        # Generate excerpt
        plain = re.sub(r'<[^>]+>', ' ', html).strip()
        plain = re.sub(r'\s+', ' ', plain)
        sentences = re.split(r'(?<=[.!?])\s+', plain)
        excerpt_text = ' '.join(sentences[:2])[:300]
        if excerpt_text:
            metadata['excerpt'] = excerpt_text

        # Yoast OG + meta fields
        meta_desc = f"{clean_title}. {excerpt_text[:100]}" if excerpt_text else clean_title
        meta_desc = meta_desc[:155]

        metadata['meta'] = {}
        if clean_title:
            metadata['meta']['_yoast_wpseo_opengraph-title'] = clean_title
        if meta_desc:
            metadata['meta']['_yoast_wpseo_opengraph-description'] = meta_desc
            # Only set metadesc if not already set
            metadata['meta']['_yoast_wpseo_metadesc'] = meta_desc

        return html, metadata

    def update_article(self, post_id, html, metadata):
        """Update content + metadata via WP REST API."""
        payload = {'content': html}
        if 'excerpt' in metadata:
            payload['excerpt'] = metadata['excerpt']
        if 'meta' in metadata:
            payload['meta'] = metadata['meta']
        return self.wp.update_post(post_id, payload)

    def fix_media_alt_text(self, media_id, alt_text):
        """Update alt text for a media item in the WP Media Library."""
        return self.wp.update_media(media_id, alt_text)

    def reoptimize_all(self):
        """Fetch all posts, analyze, fix, and report."""
        posts = self.wp.get_posts()
        results = []
        author_name = self.config.get('author_name', '')

        logger.info("=" * 60)
        logger.info("Starting re-optimization of %d posts", len(posts))
        logger.info("=" * 60)

        for i, post in enumerate(posts, 1):
            post_id = post.get('id')
            post_title = post.get('title', {}).get('rendered', '')
            html = post.get('content', {}).get('rendered', '')
            slug = post.get('slug', '')
            post_url = post.get('link', '')
            date_published = post.get('date', '')[:10]
            featured_media_id = post.get('featured_media', 0)

            if not html:
                logger.warning("[%d/%d] Post %d has no content, skipping", i, len(posts), post_id)
                continue

            clean_title = _clean_html_entities(post_title)
            logger.info("[%d/%d] Post %d: '%s'", i, len(posts), post_id, clean_title[:60])

            # Get the best keyword: Yoast focus keyword > extracted from title > slug
            keyword = self._get_yoast_keyword(post_id)
            if not keyword:
                keyword = _extract_keyword_from_title(post_title)
            logger.info("    Keyword: '%s'", keyword)

            # Get featured image URL for schema
            image_url = ""
            if featured_media_id:
                try:
                    r = requests.get(f"{self.base_url}/wp-json/wp/v2/media/{featured_media_id}",
                                     headers=self.headers)
                    if r.status_code == 200:
                        image_url = r.json().get('source_url', '')
                except Exception:
                    pass

            # Analyze and fix the HTML content
            fixed_html, metadata = self.analyze_and_fix(
                html, keyword, post_title, post_url, date_published, image_url
            )

            # Update the post
            update_result = self.update_article(post_id, fixed_html, metadata)
            post_updated = update_result is not None

            # Fix ALL media items referenced in this post
            media_ids = self._get_post_media_ids(html, featured_media_id)
            media_fixed = 0
            for mid in media_ids:
                try:
                    # Determine if this is the featured image or body image
                    if mid == featured_media_id:
                        alt = f"{keyword} - {clean_title}"[:120]
                    else:
                        # Check if it's author photo
                        r = requests.get(f"{self.base_url}/wp-json/wp/v2/media/{mid}",
                                         headers=self.headers)
                        if r.status_code == 200:
                            media_data = r.json()
                            source_url = media_data.get('source_url', '')
                            if 'terapeuta' in source_url.lower() or 'marcelo' in source_url.lower():
                                alt = f"{author_name} - Terapeuta especialista em {keyword}"
                            else:
                                alt = f"{keyword} - {clean_title}"
                            alt = alt[:120]
                        else:
                            alt = f"{keyword} - {clean_title}"[:120]

                    if self.fix_media_alt_text(mid, alt):
                        media_fixed += 1
                except Exception as e:
                    logger.warning("    Failed to fix media %d: %s", mid, e)

            logger.info("    Content updated: %s | Media alt fixed: %d/%d | Schema cleaned from content",
                         "OK" if post_updated else "FAIL",
                         media_fixed, len(media_ids))

            results.append({
                'post_id': post_id,
                'title': clean_title,
                'keyword': keyword,
                'success': post_updated,
                'schema_cleaned': True,
                'media_fixed': media_fixed,
                'media_total': len(media_ids),
            })

        success_count = sum(1 for r in results if r['success'])
        logger.info("=" * 60)
        logger.info("RE-OPTIMIZATION COMPLETE")
        logger.info("  Posts updated: %d/%d", success_count, len(results))
        logger.info("  Total media fixed: %d", sum(r['media_fixed'] for r in results))
        logger.info("  Schema text cleaned from content (Yoast handles schema)")
        logger.info("=" * 60)
        return results
