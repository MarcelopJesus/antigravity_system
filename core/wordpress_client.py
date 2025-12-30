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
        headers["Content-Type"] = "image/jpeg" # Assume JPEG for now
        
        r = requests.post(url, headers=headers, data=image_data)
        if r.status_code == 201:
            return r.json().get('id'), r.json().get('source_url')
        return None, None

    def create_post(self, title, content, featured_media_id=None, status='draft'):
        """
        Creates a new post.
        """
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        payload = {
            'title': title,
            'content': content,
            'status': status
        }
        if featured_media_id:
            payload['featured_media'] = featured_media_id

        r = requests.post(url, headers=self.headers, json=payload)
        r.raise_for_status()
        return r.json()
