import requests
import base64
from core.logger import get_logger

logger = get_logger(__name__)


class WordPressClient:
    def __init__(self, base_url, username, app_password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.headers = {
            "Authorization": "Basic " + base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        }

    def verify_auth(self):
        """Check if connection works."""
        try:
            r = requests.get(f"{self.base_url}/wp-json/wp/v2/users/me", headers=self.headers)
            if r.status_code == 200:
                logger.info("WordPress auth verified for %s", self.base_url)
                return True
            logger.error("WordPress auth failed for %s (status=%d)", self.base_url, r.status_code)
            return False
        except requests.RequestException as e:
            logger.error("WordPress connection failed for %s: %s", self.base_url, e)
            return False

    def upload_media(self, image_data, filename, alt_text=""):
        """
        Uploads an image to WordPress Media Library and sets alt text.
        """
        url = f"{self.base_url}/wp-json/wp/v2/media"
        headers = self.headers.copy()
        headers["Content-Disposition"] = f"attachment; filename={filename}"

        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
        content_types = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'
        }
        headers["Content-Type"] = content_types.get(ext, "image/jpeg")

        try:
            r = requests.post(url, headers=headers, data=image_data)
        except requests.RequestException as e:
            logger.error("Media upload connection failed for '%s': %s", filename, e)
            return None, None
        if r.status_code == 201:
            media_id = r.json().get('id')
            media_url = r.json().get('source_url')
            logger.info("Media uploaded: %s (ID: %s)", filename, media_id)

            if alt_text and media_id:
                self.update_media(media_id, alt_text)

            return media_id, media_url

        logger.error("Media upload failed for '%s' (status=%d): %s", filename, r.status_code, r.text[:200])
        return None, None

    def update_media(self, media_id, alt_text):
        """Update media alt text via WP REST API."""
        url = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
        payload = {"alt_text": alt_text}
        try:
            r = requests.post(url, headers=self.headers, json=payload)
            if r.status_code == 200:
                logger.info("Media alt text updated (ID: %s): '%s'", media_id, alt_text[:60])
                return True
            logger.warning("Failed to update media alt text (ID: %s, status=%d)", media_id, r.status_code)
            return False
        except requests.RequestException as e:
            logger.warning("Failed to update media alt text (ID: %s): %s", media_id, e)
            return False

    def create_post(self, title, content, featured_media_id=None, status='publish',
                     yoast_keyword=None, yoast_meta_desc=None, slug=None,
                     excerpt=None, og_title=None, og_description=None):
        """
        Creates a new post with Yoast SEO support and complete payload.
        """
        url = f"{self.base_url}/wp-json/wp/v2/posts"

        payload = {
            'title': title,
            'content': content,
            'status': status,
            'meta': {}
        }

        if slug:
            payload['slug'] = slug

        if excerpt:
            payload['excerpt'] = excerpt

        if yoast_keyword:
            payload['meta']['_yoast_wpseo_focuskw'] = yoast_keyword

        if yoast_meta_desc:
            payload['meta']['_yoast_wpseo_metadesc'] = yoast_meta_desc

        if og_title:
            payload['meta']['_yoast_wpseo_opengraph-title'] = og_title

        if og_description:
            payload['meta']['_yoast_wpseo_opengraph-description'] = og_description

        if not payload['meta']:
            del payload['meta']

        if featured_media_id:
            payload['featured_media'] = featured_media_id

        try:
            r = requests.post(url, headers=self.headers, json=payload)
        except requests.RequestException as e:
            logger.error("WordPress post creation failed (network): %s", e)
            raise

        # Retry without meta if Yoast keys not registered
        if r.status_code == 400 and 'meta' in r.text:
            logger.warning("Could not update Yoast Meta. Retrying without meta fields.")
            if 'meta' in payload:
                del payload['meta']
                try:
                    r = requests.post(url, headers=self.headers, json=payload)
                except requests.RequestException as e:
                    logger.error("WordPress post creation retry failed (network): %s", e)
                    raise

        r.raise_for_status()
        post_data = r.json()
        logger.info("Post created: '%s' (ID: %s, status: %s)", title, post_data.get('id'), status)
        return post_data

    def get_posts(self, per_page=100, status="publish"):
        """Fetch all published posts from WordPress."""
        posts = []
        page = 1
        while True:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            params = {"per_page": per_page, "page": page, "status": status}
            try:
                r = requests.get(url, headers=self.headers, params=params)
                if r.status_code != 200:
                    break
                batch = r.json()
                if not batch:
                    break
                posts.extend(batch)
                if len(batch) < per_page:
                    break
                page += 1
            except requests.RequestException as e:
                logger.error("Failed to fetch posts (page %d): %s", page, e)
                break
        logger.info("Fetched %d posts from WordPress", len(posts))
        return posts

    def update_post(self, post_id, payload):
        """Update an existing post via WP REST API."""
        url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        try:
            r = requests.post(url, headers=self.headers, json=payload)
            if r.status_code == 200:
                logger.info("Post updated (ID: %s)", post_id)
                return r.json()
            logger.warning("Failed to update post (ID: %s, status=%d): %s", post_id, r.status_code, r.text[:200])
            return None
        except requests.RequestException as e:
            logger.error("Failed to update post (ID: %s): %s", post_id, e)
            return None
