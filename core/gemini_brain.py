import google.generativeai as genai
import os
import requests
from config.settings import GOOGLE_API_KEYS_LIST
from config.prompts import RESEARCH_AND_WRITE_PROMPT, REWRITE_WITH_PERSONA_PROMPT, IMAGE_PROMPT_GENERATION

class GeminiBrain:
    def __init__(self):
        if not GOOGLE_API_KEYS_LIST:
            raise ValueError("GOOGLE_API_KEYS_LIST is not set or empty in environment.")
        
        self.api_keys = GOOGLE_API_KEYS_LIST
        self.current_key_index = 0
        self._configure_current_key()
        
        # Tools: Google Search
        self.tools = [
            {"google_search": {}} 
        ]
        
    def _configure_current_key(self):
        """Configures the Gemini library with the current key."""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        # print(f"     [DEBUG] Switch to API Key index: {self.current_key_index}")

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
                # Naive check for permission/quota errors. 
                # Ideally check for specific error codes (400, 429, 403)
                error_str = str(e)
                if "400" in error_str or "429" in error_str or "403" in error_str or "API key expired" in error_str:
                     print(f"     ⚠️ API Error with key #{self.current_key_index + 1}: {e}")
                     if not self._rotate_key():
                         raise e
                     attempts += 1
                else:
                    # Reraise other errors immediately
                    raise e
        
        raise Exception("All API keys failed.")

    def research_and_draft(self, keyword):
        """
        Uses Gemini 2.0 Flash to research the keyword and write a draft.
        """
        def _task():
            model = genai.GenerativeModel('gemini-2.0-flash-exp') 
            prompt = RESEARCH_AND_WRITE_PROMPT.format(keyword=keyword)
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

    def refine_with_persona(self, draft_text, persona):
        """
        Rewrites the draft using a specific persona.
        """
        def _task():
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            prompt = REWRITE_WITH_PERSONA_PROMPT.format(persona=persona) + "\n\nTEXTO ORIGINAL:\n" + draft_text
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

    def generate_image_prompts(self, article_text):
        """
        Asks Gemini to describe 4 images for the article.
        """
        def _task():
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            prompt = IMAGE_PROMPT_GENERATION + "\n\nARTIGO:\n" + article_text[:2000]
            response = model.generate_content(prompt)
            return response.text

        return self._execute_with_retry(_task)

    def generate_images(self, image_prompt):
        """
        Uses standard REST API for Imagen 3 generation.
        Manually handles rotation since it uses `requests`.
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
                    "sampleCount": 3,
                    "aspectRatio": "16:9" 
                }
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    print(f"     ⚠️ Imagen API Error (Key #{self.current_key_index + 1}): {response.text}")
                    # Force rotation if it looks like an auth/quota issue
                    if response.status_code in [400, 401, 403, 429]:
                        if self._rotate_key():
                            attempts += 1
                            continue
                    return [] # Non-retryable error or no keys left
                
                # Success
                data = response.json()
                images_b64 = []
                if 'predictions' in data:
                    for pred in data['predictions']:
                        if 'bytesBase64Encoded' in pred:
                            images_b64.append(pred['bytesBase64Encoded'])
                        elif 'mimeType' in pred and 'bytesBase64Encoded' in pred:
                                images_b64.append(pred['bytesBase64Encoded'])
                return images_b64

            except Exception as e:
                print(f"     ❌ Image Generation Connection Failed: {e}")
                if self._rotate_key():
                     attempts += 1
                     continue
                return []
        
        return []
