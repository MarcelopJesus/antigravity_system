"""Tests for WordPressClient (Story 1.7)."""
import pytest
from unittest.mock import patch, MagicMock
from core.wordpress_client import WordPressClient


@pytest.fixture
def wp_client():
    return WordPressClient("https://example.com", "admin", "app-pass-123")


class TestVerifyAuth:
    def test_auth_success(self, wp_client):
        with patch("core.wordpress_client.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert wp_client.verify_auth() is True

    def test_auth_failure(self, wp_client):
        with patch("core.wordpress_client.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=401)
            assert wp_client.verify_auth() is False

    def test_auth_connection_error(self, wp_client):
        import requests as req_lib
        with patch("core.wordpress_client.requests.get") as mock_get:
            mock_get.side_effect = req_lib.RequestException("Connection refused")
            assert wp_client.verify_auth() is False


class TestUploadMedia:
    def test_upload_success(self, wp_client):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 42, "source_url": "https://example.com/image.png"}

        with patch("core.wordpress_client.requests.post", return_value=mock_response):
            media_id, media_url = wp_client.upload_media(b"fake-image-data", "test.png")

        assert media_id == 42
        assert media_url == "https://example.com/image.png"

    def test_upload_failure(self, wp_client):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("core.wordpress_client.requests.post", return_value=mock_response):
            media_id, media_url = wp_client.upload_media(b"fake-image-data", "test.png")

        assert media_id is None
        assert media_url is None


class TestCreatePost:
    def test_create_post_success(self, wp_client):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 99,
            "link": "https://example.com/test-post/",
            "status": "publish"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("core.wordpress_client.requests.post", return_value=mock_response):
            result = wp_client.create_post(
                title="Test Post",
                content="<p>Content</p>",
                yoast_keyword="test",
                yoast_meta_desc="Test description"
            )

        assert result["id"] == 99
        assert result["link"] == "https://example.com/test-post/"

    def test_create_post_with_featured_image(self, wp_client):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 100, "link": "https://example.com/post/"}
        mock_response.raise_for_status = MagicMock()

        with patch("core.wordpress_client.requests.post", return_value=mock_response) as mock_post:
            wp_client.create_post(
                title="Post with Image",
                content="<p>Content</p>",
                featured_media_id=42
            )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["featured_media"] == 42

    def test_create_post_yoast_meta_fallback(self, wp_client):
        """When Yoast meta keys fail, should retry without meta."""
        # First call fails with meta error
        mock_fail = MagicMock()
        mock_fail.status_code = 400
        mock_fail.text = '{"message": "Invalid meta key"}'

        # Second call succeeds without meta
        mock_success = MagicMock()
        mock_success.status_code = 201
        mock_success.json.return_value = {"id": 101, "link": "https://example.com/post/"}
        mock_success.raise_for_status = MagicMock()

        with patch("core.wordpress_client.requests.post", side_effect=[mock_fail, mock_success]) as mock_post:
            result = wp_client.create_post(
                title="Post",
                content="<p>Content</p>",
                yoast_keyword="key",
                yoast_meta_desc="desc"
            )

        assert result["id"] == 101
        assert mock_post.call_count == 2
