import requests
import base64

class WordPressClient:
    def __init__(self, base_url, username, app_password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.headers = {
            "Authorization": "Basic " + base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        }

    def verify_auth(self):
        """Check if connection works"""
        r = requests.get(f"{self.base_url}/wp-json/wp/v2/users/me", headers=self.headers)
        return r.status_code == 200

    def upload_media(self, image_data, filename):
        """
        Uploads an image to WordPress Media Library.
        image_data: bytes
        filename: str
        """
        url = f"{self.base_url}/wp-json/wp/v2/media"
        headers = self.headers.copy()
        headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        # Detect Content-Type from extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
        content_types = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'
        }
        headers["Content-Type"] = content_types.get(ext, "image/jpeg")
        
        r = requests.post(url, headers=headers, data=image_data)
        if r.status_code == 201:
            return r.json().get('id'), r.json().get('source_url')
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
        
        # Yoast SEO Integration (JSON API fields might vary by version, using standard meta keys)
        # Note: To write to these via REST API, the meta keys must be registered in WP or allowed.
        # Common keys for Yoast:
        if yoast_keyword:
            payload['meta']['_yoast_wpseo_focuskw'] = yoast_keyword
        
        if yoast_meta_desc:
            payload['meta']['_yoast_wpseo_metadesc'] = yoast_meta_desc
            
        # Clean up meta if empty
        if not payload['meta']:
            del payload['meta']

        if featured_media_id:
            payload['featured_media'] = featured_media_id

        r = requests.post(url, headers=self.headers, json=payload)
        
        # Error handling for meta keys not registered
        if r.status_code == 400 and 'meta' in r.text:
             print("     ⚠️ Warning: Could not update Yoast Meta. Keys might not be registered in REST API.")
             # Retry without meta
             if 'meta' in payload:
                 del payload['meta']
                 r = requests.post(url, headers=self.headers, json=payload)

        r.raise_for_status()
        return r.json()
