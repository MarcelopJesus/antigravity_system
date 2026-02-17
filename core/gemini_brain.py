import google.generativeai as genai
import os
import requests
import json
import re
import glob
import random
import markdown
from pathlib import Path
from config.settings import GOOGLE_API_KEYS_LIST, GEMINI_MODEL_NAME
from config.prompts import (
    CONTENT_ANALYST_PROMPT,
    SENIOR_WRITER_PROMPT,
    TRI_HUMANIZER_PROMPT,
    CONVERSION_EDITOR_PROMPT,
    IMAGE_PROMPT_GENERATION,
    GROWTH_HACKER_PROMPT
)
from core.logger import get_logger

logger = get_logger(__name__)


class GeminiBrain:
    def __init__(self, knowledge_base_path=None):
        if not GOOGLE_API_KEYS_LIST:
            raise ValueError("GOOGLE_API_KEYS_LIST is not set or empty in environment.")

        self.api_keys = GOOGLE_API_KEYS_LIST
        self.current_key_index = 0
        self.knowledge_base_path = knowledge_base_path or "knowledge_base"
        self._configure_current_key()

    def _configure_current_key(self):
        """Configures the Gemini library with the current key."""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        logger.debug("Configured Gemini with API key #%d", self.current_key_index + 1)

    def _rotate_key(self):
        """Rotates to the next available API key."""
        if len(self.api_keys) <= 1:
            logger.error("Only one API key available, cannot rotate.")
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_current_key()
        logger.info("Rotating to API Key #%d", self.current_key_index + 1)
        return True

    def _execute_with_retry(self, func, *args, **kwargs):
        """Executes a function with retry logic for API keys."""
        max_retries = len(self.api_keys)
        attempts = 0

        while attempts < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "400" in error_str or "429" in error_str or "403" in error_str or "API key expired" in error_str:
                    logger.warning("API Error with key #%d: %s", self.current_key_index + 1, e)
                    if not self._rotate_key():
                        raise e
                    attempts += 1
                else:
                    raise e

        raise Exception("All API keys failed.")

    # =========================================================================
    # KNOWLEDGE BASE LOADING (V3 — Flexible Multi-File System)
    # =========================================================================
    def _load_knowledge_base(self, file_filter=None):
        """
        Reads files from company-specific knowledge_base folder.

        Args:
            file_filter: Optional list of substrings to filter files.
                         If None, loads all TRI_* and *premium* files.
                         Example: ["essencia", "voz"] loads TRI_ESSENCIA.txt and TRI_VOZ.txt

        Returns empty string if no knowledge base exists.
        """
        kb_content = ""
        try:
            kb_path = self.knowledge_base_path
            if not os.path.exists(kb_path):
                logger.info("No knowledge base found at '%s'. Using AI's general knowledge.", kb_path)
                return ""

            files = glob.glob(f"{kb_path}/*.txt")
            if not files:
                logger.info("No .txt files in '%s'. Using AI's general knowledge.", kb_path)
                return ""

            # Default filter: load optimized TRI files + premium
            if file_filter is None:
                file_filter = ["tri_essencia", "tri_voz", "premium"]

            loaded_count = 0
            for file_path in files:
                filename = os.path.basename(file_path).lower()

                # Check if file matches any filter pattern
                should_load = any(pattern in filename for pattern in file_filter)

                if should_load:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        kb_content += f"\n--- ARQUIVO: {os.path.basename(file_path)} ---\n{content}\n"
                        loaded_count += 1
                        logger.info("Loaded KB: %s (%s chars)", os.path.basename(file_path), f"{len(content):,}")
                else:
                    logger.debug("Skipped KB file: %s (not in filter)", os.path.basename(file_path))

            if not kb_content:
                logger.warning("No matching KB files found for filter %s.", file_filter)
            else:
                logger.info("Loaded %d KB file(s) (%s total chars)", loaded_count, f"{len(kb_content):,}")

            return kb_content
        except Exception as e:
            logger.error("Could not load knowledge base: %s", e)
            return ""

    def _load_voice_guide(self):
        """
        Loads just the TRI_VOZ.txt file for the Humanizer agent.
        Returns the voice guide content or empty string.
        """
        try:
            kb_path = self.knowledge_base_path
            voz_files = glob.glob(f"{kb_path}/*VOZ*.txt") + glob.glob(f"{kb_path}/*voz*.txt")

            if voz_files:
                with open(voz_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info("Voice Guide loaded: %s (%s chars)", os.path.basename(voz_files[0]), f"{len(content):,}")
                    return content

            logger.warning("No TRI_VOZ file found. Humanizer will use default voice settings.")
            return ""
        except Exception as e:
            logger.error("Could not load voice guide: %s", e)
            return ""

    # =========================================================================
    # 1. ANALISTA DE CONTEUDO
    # =========================================================================
    def analyze_and_plan(self, keyword, links_inventory):
        """
        Agent 1: Creates the strategic outline (JSON).
        Loads TRI_ESSENCIA + TRI_Premium for maximum context.
        """
        kb_text = self._load_knowledge_base(file_filter=["tri_essencia", "premium"])

        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)

            # Format links from list of dicts to string
            if isinstance(links_inventory, list):
                links_text = "\n".join([f"- {item.get('keyword', 'Link')}: {item.get('url', '#')}" for item in links_inventory])
            else:
                links_text = str(links_inventory)

            # Inject KB into prompt
            prompt = CONTENT_ANALYST_PROMPT.format(
                keyword=keyword,
                links_list=links_text,
                knowledge_base=kb_text
            )
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return response.text

        raw_json = self._execute_with_retry(_task)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            # Fallback cleanup if needed
            cleaned = raw_json.replace("```json", "").replace("```", "")
            return json.loads(cleaned)

    # =========================================================================
    # 2. REDATOR SENIOR
    # =========================================================================
    def write_article_body(self, outline_json):
        """
        Agent 2: Writes the full content based on the plan.
        Loads TRI_ESSENCIA for conceptual grounding.
        """
        kb_text = self._load_knowledge_base(file_filter=["tri_essencia", "premium"])

        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = SENIOR_WRITER_PROMPT.format(
                outline_json=json.dumps(outline_json, indent=2, ensure_ascii=False),
                knowledge_base=kb_text
            )
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

    # =========================================================================
    # 3. HUMANIZADOR TRI (Voz do Marcelo Jesus)
    # =========================================================================
    def humanize_with_tri_voice(self, draft_html):
        """
        Agent 3: Transforms technically correct content into authentic
        Marcelo Jesus voice using TRI_VOZ.txt as reference.
        """
        voice_guide = self._load_voice_guide()

        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = TRI_HUMANIZER_PROMPT.format(
                voice_guide=voice_guide,
                draft_html=draft_html
            )
            response = model.generate_content(prompt)
            return response.text

        raw_text = self._execute_with_retry(_task)

        # Clean up any wrapping code blocks
        clean_text = re.sub(r"^```html\s*", "", raw_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"^```\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"```$", "", clean_text, flags=re.IGNORECASE)

        return clean_text.strip()

    # =========================================================================
    # 4. EDITOR DE CONVERSAO & SEO
    # =========================================================================
    def edit_and_refine(self, draft_html):
        """
        Agent 4: Polishes the content, check constraints and HTML structure.
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = CONVERSION_EDITOR_PROMPT.format(draft_html=draft_html)
            response = model.generate_content(prompt)
            return response.text

        raw_text = self._execute_with_retry(_task)

        # CLEANUP LOGIC: Remove Markdown blocks usually returned by LLMs
        clean_text = re.sub(r"^```html\s*", "", raw_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"^```\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"```$", "", clean_text, flags=re.IGNORECASE)

        # Remove conversational prefixes
        if "<h1>" in clean_text:
            clean_text = clean_text[clean_text.find("<h1>"):]

        # SAFETY NET: If text still looks like Markdown, force convert
        if "##" in clean_text or "**" in clean_text:
            logger.warning("Detected raw Markdown in editor output. Converting to HTML...")
            html = markdown.markdown(clean_text)
            return html.strip()

        return clean_text.strip()

    # =========================================================================
    # 5. DIRETOR DE ARTE (Editorial Premium)
    # =========================================================================
    def generate_image_prompts(self, final_article):
        """
        Agent 5: Creates 2 visual prompts (Capa + Final).
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            article_context = final_article[:8000]
            prompt = IMAGE_PROMPT_GENERATION.format(article_content=article_context)
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

    def _is_valid_image(self, filepath):
        """
        Checks if a file is a real JPEG/PNG/WebP image by reading magic bytes.
        """
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

    def get_real_author_photo(self):
        """
        Returns the binary data of a real author photo from knowledge_base/images/.
        Rotates through available photos to avoid repetition across articles.
        """
        images_path = Path(self.knowledge_base_path) / "images"

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

    def generate_final_images(self, image_prompt):
        """
        Executes the generation on Imagen API.
        """
        max_retries = len(self.api_keys)
        attempts = 0

        while attempts < max_retries:
            current_key = self.api_keys[self.current_key_index]
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
                    logger.warning("Imagen API Error (Key #%d): status=%d", self.current_key_index + 1, response.status_code)
                    if response.status_code in [400, 401, 403, 429]:
                        if self._rotate_key():
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
                if self._rotate_key():
                    attempts += 1
                    continue
                return None

        return None

    # =========================================================================
    # 6. GROWTH HACKER
    # =========================================================================
    def identify_new_topics(self, title, final_article):
        """
        Agent 6: Scans the content for gaps and suggests new topics.
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = GROWTH_HACKER_PROMPT.format(title=title)
            response = model.generate_content(prompt)
            return response.text

        raw_suggestions = self._execute_with_retry(_task)
        suggestions = [line.strip().replace("-", "").strip() for line in raw_suggestions.split('\n') if line.strip()]
        return suggestions[:2]
