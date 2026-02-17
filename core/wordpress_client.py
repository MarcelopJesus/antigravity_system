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

    def upload_media(self, image_data, filename):
        """
        Uploads an image to WordPress Media Library.
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

        r = requests.post(url, headers=headers, data=image_data)
        if r.status_code == 201:
            media_id = r.json().get('id')
            media_url = r.json().get('source_url')
            logger.info("Media uploaded: %s (ID: %s)", filename, media_id)
            return media_id, media_url

        logger.error("Media upload failed for '%s' (status=%d): %s", filename, r.status_code, r.text[:200])
        return None, None

    def create_post(self, title, content, featured_media_id=None, status='publish', yoast_keyword=None, yoast_meta_desc=None):
        """
        Creates a new post with Yoast SEO support.
        """
        url = f"{self.base_url}/wp-json/wp/v2/posts"

        payload = {
            'title': title,
            'content': content,
            'status': status,
            'meta': {}
        }

        if yoast_keyword:
            payload['meta']['_yoast_wpseo_focuskw'] = yoast_keyword

        if yoast_meta_desc:
            payload['meta']['_yoast_wpseo_metadesc'] = yoast_meta_desc

        if not payload['meta']:
            del payload['meta']

        if featured_media_id:
            payload['featured_media'] = featured_media_id

        r = requests.post(url, headers=self.headers, json=payload)

        # Retry without meta if Yoast keys not registered
        if r.status_code == 400 and 'meta' in r.text:
            logger.warning("Could not update Yoast Meta. Retrying without meta fields.")
            if 'meta' in payload:
                del payload['meta']
                r = requests.post(url, headers=self.headers, json=payload)

        r.raise_for_status()
        post_data = r.json()
        logger.info("Post created: '%s' (ID: %s, status: %s)", title, post_data.get('id'), status)
        return post_data
