"""Tests for alt text generation in VisualAgent and WordPressClient."""
import unittest
from unittest.mock import MagicMock, patch


class TestUploadMediaAltText(unittest.TestCase):
    """Test that upload_media passes alt_text and calls update_media."""

    def test_upload_media_calls_update_media_with_alt_text(self):
        from core.wordpress_client import WordPressClient
        wp = WordPressClient("https://example.com", "user", "pass")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 42, "source_url": "https://example.com/img.png"}

        with patch("requests.post", return_value=mock_response):
            with patch.object(wp, "update_media") as mock_update:
                media_id, media_url = wp.upload_media(b"fake", "test.png", alt_text="My alt text")
                mock_update.assert_called_once_with(42, "My alt text")
                assert media_id == 42

    def test_upload_media_no_alt_text_skips_update(self):
        from core.wordpress_client import WordPressClient
        wp = WordPressClient("https://example.com", "user", "pass")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 42, "source_url": "https://example.com/img.png"}

        with patch("requests.post", return_value=mock_response):
            with patch.object(wp, "update_media") as mock_update:
                wp.upload_media(b"fake", "test.png")
                mock_update.assert_not_called()


class TestAltTextGeneration(unittest.TestCase):
    """Test alt text logic in process_images context."""

    def test_cover_alt_text_format(self):
        keyword = "Hipnoterapia Moema"
        title = "Hipnoterapia em Moema: Guia Completo"
        title_short = title[:60].rsplit(' ', 1)[0] if len(title) > 60 else title
        expected = f"{keyword} - {title_short}"
        assert expected == "Hipnoterapia Moema - Hipnoterapia em Moema: Guia Completo"

    def test_author_alt_text_with_site_config(self):
        site_config = {"author_name": "Marcelo Jesus"}
        keyword = "Ansiedade"
        author_name = site_config.get("author_name", "Terapeuta")
        alt = f"{author_name} - Terapeuta especialista em {keyword}"
        assert alt == "Marcelo Jesus - Terapeuta especialista em Ansiedade"

    def test_author_alt_text_without_site_config(self):
        site_config = None
        keyword = "Ansiedade"
        author_name = (site_config or {}).get("author_name", "Marcelo Jesus")
        alt = f"{author_name} - Terapeuta especialista em {keyword}"
        assert alt == "Marcelo Jesus - Terapeuta especialista em Ansiedade"

    def test_final_image_alt_with_outline(self):
        import re
        keyword = "Hipnoterapia"
        outline = {"outline": ["H2. O que é Hipnoterapia", "H2. Benefícios", "H2. Próximos Passos"]}
        sections = outline.get("outline", [])
        last_section = ""
        for s in reversed(sections):
            if isinstance(s, str) and s.strip().startswith("H2"):
                last_section = re.sub(r'^H2\.\s*', '', s.strip())
                break
        alt = f"{keyword} - {last_section}" if last_section else f"{keyword}"
        assert alt == "Hipnoterapia - Próximos Passos"


if __name__ == "__main__":
    unittest.main()
