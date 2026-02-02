import google.generativeai as genai
import os
import requests
import json
import re
import glob
import markdown
from config.settings import GOOGLE_API_KEYS_LIST, GEMINI_MODEL_NAME
from config.prompts import (
    CONTENT_ANALYST_PROMPT,
    SENIOR_WRITER_PROMPT,
    CONVERSION_EDITOR_PROMPT,
    IMAGE_PROMPT_GENERATION,
    GROWTH_HACKER_PROMPT
)

class GeminiBrain:
    def __init__(self, knowledge_base_path=None):
        if not GOOGLE_API_KEYS_LIST:
            raise ValueError("GOOGLE_API_KEYS_LIST is not set or empty in environment.")
        
        self.api_keys = GOOGLE_API_KEYS_LIST
        self.current_key_index = 0
        self.knowledge_base_path = knowledge_base_path or "knowledge_base"  # Default fallback
        self._configure_current_key()
        
    def _configure_current_key(self):
        """Configures the Gemini library with the current key."""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)

    def _rotate_key(self):
        """Rotates to the next available API key."""
        if len(self.api_keys) <= 1:
            print("     ❌ Only one API key available, cannot rotate.")
            return False
            
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_current_key()
        print(f"     🔄 Rotating to API Key #{self.current_key_index + 1}...")
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
                     print(f"     ⚠️ API Error with key #{self.current_key_index + 1}: {e}")
                     if not self._rotate_key():
                         raise e
                     attempts += 1
                else:
                    raise e
        
        raise Exception("All API keys failed.")

    def _load_knowledge_base(self):
        """
        Reads files from company-specific knowledge_base folder.
        Returns empty string if no knowledge base exists (some companies may not have one).
        """
        kb_content = ""
        try:
            # Use company-specific path
            kb_path = self.knowledge_base_path
            if not os.path.exists(kb_path):
                print(f"     [Brain] No knowledge base found at '{kb_path}'. Using AI's general knowledge.")
                return ""
            
            files = glob.glob(f"{kb_path}/*.txt")
            if not files:
                print(f"     [Brain] No .txt files in '{kb_path}'. Using AI's general knowledge.")
                return ""
            
            for file_path in files:
                filename = os.path.basename(file_path).lower()
                
                # FILTER: Only load the Premium file for now (80/20 Strategy)
                if "premium" in filename:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        kb_content += f"\n--- ARQUIVO: {os.path.basename(file_path)} ---\n{content}\n"
                        print(f"     [Brain] Loaded Base: {os.path.basename(file_path)}")
                else:
                    print(f"     [Brain] Skipping large file (80/20): {os.path.basename(file_path)}")
            
            if not kb_content:
                print(f"     [Brain] No premium knowledge base files found. Using AI's general knowledge.")
            
            return kb_content
        except Exception as e:
            print(f"     [Brain] Warning: Could not load knowledge base: {e}")
            return ""

    # =========================================================================
    # 1. ANALISTA DE CONTEÚDO
    # =========================================================================
    def analyze_and_plan(self, keyword, links_inventory):
        """
        Agent 1: Creates the strategic outline (JSON).
        Now with Knowledge Base injection!
        """
        kb_text = self._load_knowledge_base()
        
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
        except:
            # Fallback cleanup if needed
            cleaned = raw_json.replace("```json", "").replace("```", "")
            return json.loads(cleaned)

    # =========================================================================
    # 2. REDATOR SÊNIOR
    # =========================================================================
    def write_article_body(self, outline_json):
        """
        Agent 2: Writes the full content based on the plan.
        Now with Knowledge Base injection!
        """
        kb_text = self._load_knowledge_base()

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
    # 3. EDITOR DE CONVERSÃO & SEO
    # =========================================================================
    def edit_and_refine(self, draft_html):
        """
        Agent 3: Polishes the content, check constraints and HTML structure.
        Uses Python-based Markdown conversion as a fallback safety net.
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = CONVERSION_EDITOR_PROMPT.format(draft_html=draft_html)
            response = model.generate_content(prompt)
            return response.text

        raw_text = self._execute_with_retry(_task)
        
        # CLEANUP LOGIC: Remove Markdown blocks usually returned by LLMs
        # Remove ```html and ``` at start/end
        clean_text = re.sub(r"^```html\s*", "", raw_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"^```\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"```$", "", clean_text, flags=re.IGNORECASE)
        
        # Remove conversational prefixes if they still exist (Naive check)
        # Look for the first <h1>. Everything before it is likely garbage.
        if "<h1>" in clean_text:
            clean_text = clean_text[clean_text.find("<h1>"):]
            
        # SAFETY NET: If the text still looks like Markdown (has ## or **), force convert
        # Check for common markdown headers or bolding that wasn't converted
        if "##" in clean_text or "**" in clean_text:
            print("     [Brain] Warning: Detected raw Markdown. Converting to HTML...")
            html = markdown.markdown(clean_text)
            return html.strip()
            
        return clean_text.strip()

    # =========================================================================
    # 4. DIRETOR DE ARTE
    # =========================================================================
    def generate_image_prompts(self, final_article):
        """
        Agent 4: Creates visual prompts based on the final text.
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            # Send intro + headers to give context without token overflow
            # Increased context to 4000 to ensure context for middle/end images
            brief_context = final_article[:4000] 
            
            prompt = IMAGE_PROMPT_GENERATION.format(article_content=brief_context)
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

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
                    "sampleCount": 1, # Generate 1 high quality per prompt
                    "aspectRatio": "16:9" 
                }
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    print(f"     ⚠️ Imagen API Error (Key #{self.current_key_index + 1}): {response.text}")
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
                        elif 'mimeType' in pred and 'bytesBase64Encoded' in pred:
                             return pred['bytesBase64Encoded']
                return None

            except Exception as e:
                print(f"     ❌ Image Generation Connection Failed: {e}")
                if self._rotate_key():
                     attempts += 1
                     continue
                return None
        
        return None

    # =========================================================================
    # 5. GROWTH HACKER
    # =========================================================================
    def identify_new_topics(self, title, final_article):
        """
        Agent 5: Scans the content for gaps and suggests new topics for the backlog.
        """
        def _task():
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            prompt = GROWTH_HACKER_PROMPT.format(title=title)
            response = model.generate_content(prompt)
            return response.text

        raw_suggestions = self._execute_with_retry(_task)
        # Simple cleanup
        suggestions = [line.strip().replace("-", "").strip() for line in raw_suggestions.split('\n') if line.strip()]
        return suggestions[:2]
