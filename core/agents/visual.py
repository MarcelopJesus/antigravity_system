"""VisualAgent — Generates image prompts and handles image processing."""
import re
import base64
import requests
from pathlib import Path
from core.agents.base import BaseAgent, AgentResult
from core.logger import get_logger
from config.prompts import IMAGE_PROMPT_GENERATION

logger = get_logger(__name__)


class VisualAgent(BaseAgent):
    name = "visual"

    def _build_prompt(self, input_data):
        article_context = input_data[:8000]
        return IMAGE_PROMPT_GENERATION.format(article_content=article_context)

    def _parse_response(self, raw_text, input_data=None):
        return raw_text

    def generate_image(self, image_prompt):
        """Executes image generation on Imagen API with key rotation."""
        max_retries = len(self.llm.api_keys)
        attempts = 0

        while attempts < max_retries:
            current_key = self.llm.api_keys[self.llm.current_key_index]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={current_key}"
            headers = {'Content-Type': 'application/json'}

            payload = {
                "instances": [{"prompt": image_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9"
                }
            }

            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.warning("Imagen API Error (Key #%d): status=%d", self.llm.current_key_index + 1, response.status_code)
                    if response.status_code in [400, 401, 403, 429]:
                        if self.llm._rotate_key():
                            attempts += 1
                            continue
                    return None

                data = response.json()
                if 'predictions' in data:
                    for pred in data['predictions']:
                        if 'bytesBase64Encoded' in pred:
                            return pred['bytesBase64Encoded']
                return None

            except Exception as e:
                logger.error("Image Generation Connection Failed: %s", e)
                if self.llm._rotate_key():
                    attempts += 1
                    continue
                return None

        return None

    @staticmethod
    def _is_valid_image(filepath):
        """Checks if a file is a real JPEG/PNG/WebP image by reading magic bytes."""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(12)

            if header[:3] == b'\xff\xd8\xff':
                return True
            if header[:4] == b'\x89PNG':
                return True
            if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return True

            logger.warning("Skipping '%s' — not a real JPEG/PNG/WebP (likely HEIC)", filepath.name)
            return False
        except Exception:
            return False

    def get_real_author_photo(self, knowledge_base_path):
        """Returns the binary data of a real author photo from knowledge_base/images/."""
        images_path = Path(knowledge_base_path) / "images"

        if not images_path.exists():
            logger.warning("No images folder at '%s'. Skipping author photo.", images_path)
            return None, None

        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        candidates = [
            f for f in images_path.iterdir()
            if f.is_file() and f.suffix.lower() in valid_extensions
        ]

        photos = [f for f in candidates if self._is_valid_image(f)]

        if not photos:
            logger.warning("No valid photos found in '%s'. Skipping author photo.", images_path)
            if candidates:
                logger.info("Tip: %d file(s) found but invalid format. Convert HEIC to JPEG first.", len(candidates))
            return None, None

        # Rotation logic
        state_file = images_path / ".last_photo_index"
        last_index = 0

        try:
            if state_file.exists():
                last_index = int(state_file.read_text().strip())
        except (ValueError, OSError):
            last_index = 0

        current_index = (last_index + 1) % len(photos)
        selected_photo = sorted(photos)[current_index]

        try:
            state_file.write_text(str(current_index))
        except OSError:
            pass

        try:
            image_data = selected_photo.read_bytes()
            filename = selected_photo.name
            logger.info("Author photo selected: %s (%d valid photos in rotation)", filename, len(photos))
            return image_data, filename
        except Exception as e:
            logger.error("Error reading photo '%s': %s", selected_photo, e)
            return None, None

    def process_images(self, final_content, final_title, keyword, wp_client, knowledge_base_path,
                        site_config=None, outline=None):
        """Full image processing pipeline: generate prompts, create images, inject into HTML.

        Args:
            final_content: The article HTML content.
            final_title: The article title.
            keyword: The target keyword (for filenames).
            wp_client: WordPressClient instance for uploading.
            knowledge_base_path: Path to KB for author photos.
            site_config: Site configuration dict (for author_name, etc).
            outline: Outline dict from analyst (for section titles).

        Returns:
            (updated_content, featured_media_id, images_failed_count)
        """
        images_failed = 0
        featured_media_id = None
        slug = keyword.replace(" ", "-").lower()[:30]

        # Generate prompts
        logger.info("  5. Visual Agent: Generating Editorial Images...")
        result = self.execute(final_content)
        if not result.success:
            logger.warning("     Image prompt generation failed. Publishing without images.")
            return final_content, None, 3

        prompts_list = [p.strip() for p in result.content.split('|||') if p.strip()]

        # IMAGE 1: AI-Generated Cover
        if len(prompts_list) >= 1:
            logger.info("     Image 1 (Cover): Generating AI editorial image...")
            try:
                b64_image = self.generate_image(prompts_list[0])
                if b64_image:
                    image_data = base64.b64decode(b64_image)
                    filename = f"{slug}-capa.png"
                    title_short = final_title[:60].rsplit(' ', 1)[0] if len(final_title) > 60 else final_title
                    cover_alt = f"{keyword} - {title_short}"
                    media_id, media_url = wp_client.upload_media(image_data, filename, alt_text=cover_alt)
                    featured_media_id = media_id
                    logger.info("     Featured Image Set (ID: %s, alt: '%s')", media_id, cover_alt[:50])
                else:
                    logger.warning("     Cover image generation returned empty. Publishing without featured image.")
                    images_failed += 1
            except Exception as img_err:
                logger.warning("     Cover image failed: %s. Publishing without featured image.", img_err)
                images_failed += 1

        # IMAGE 2: AI-Generated Body Image
        if len(prompts_list) >= 2:
            logger.info("     Image 2 (Body): Generating AI editorial image...")
            try:
                b64_image = self.generate_image(prompts_list[1])
                if b64_image:
                    image_data = base64.b64decode(b64_image)
                    filename = f"{slug}-corpo.png"
                    # Use first H2 section title for alt text context
                    first_section = ""
                    if outline and isinstance(outline, dict):
                        sections = outline.get('outline', [])
                        for s in sections:
                            if isinstance(s, str) and s.strip().startswith('H2'):
                                first_section = re.sub(r'^H2\.\s*', '', s.strip())
                                break
                    body_alt = f"{keyword} - {first_section}" if first_section else f"{keyword} - {final_title}"
                    media_id, media_url = wp_client.upload_media(image_data, filename, alt_text=body_alt)

                    body_img_html = f"<figure class='wp-block-image'><img src='{media_url}' alt='{body_alt}'/></figure>"

                    if "<!-- IMG_PLACEHOLDER -->" in final_content:
                        final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", body_img_html, 1)
                        logger.info("     Body image injected into placeholder.")
                    else:
                        h2_match = re.search(r'(</h2>)', final_content)
                        if h2_match:
                            insert_pos = h2_match.end()
                            final_content = final_content[:insert_pos] + "\n" + body_img_html + "\n" + final_content[insert_pos:]
                            logger.info("     Body image inserted after first H2.")
                        else:
                            final_content += "\n" + body_img_html
                            logger.info("     Body image appended to end.")
                else:
                    logger.warning("     Body image generation returned empty. Continuing without it.")
                    images_failed += 1
            except Exception as img_err:
                logger.warning("     Body image failed: %s. Continuing without it.", img_err)
                images_failed += 1

        # IMAGE 3: AI-Generated Final
        if len(prompts_list) >= 3:
            logger.info("     Image 3 (Final): Generating AI editorial image...")
            try:
                b64_image = self.generate_image(prompts_list[2])
                if b64_image:
                    image_data = base64.b64decode(b64_image)
                    filename = f"{slug}-final.png"
                    # Use last outline section title for context, fallback to article title
                    last_section = ""
                    if outline and isinstance(outline, dict):
                        sections = outline.get('outline', [])
                        for s in reversed(sections):
                            if isinstance(s, str) and s.strip().startswith('H2'):
                                last_section = re.sub(r'^H2\.\s*', '', s.strip())
                                break
                    final_alt = f"{keyword} - {last_section}" if last_section else f"{keyword} - {final_title}"
                    media_id, media_url = wp_client.upload_media(image_data, filename, alt_text=final_alt)

                    final_img_html = f"<figure class='wp-block-image'><img src='{media_url}' alt='{final_alt}'/></figure>"

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
                    images_failed += 1
            except Exception as img_err:
                logger.warning("     Final image failed: %s. Publishing without it.", img_err)
                images_failed += 1

        return final_content, featured_media_id, images_failed
