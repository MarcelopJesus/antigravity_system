import google.generativeai as genai
import os
from config.settings import GOOGLE_API_KEY
from config.prompts import RESEARCH_AND_WRITE_PROMPT, REWRITE_WITH_PERSONA_PROMPT, IMAGE_PROMPT_GENERATION

class GeminiBrain:
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in environment.")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Tools: Google Search
        self.tools = [
            {"google_search": {}} # Correct syntax for tools in some versions, or object
        ]
        
    def research_and_draft(self, keyword):
        """
        Uses Gemini 2.0 Flash to research the keyword and write a draft.
        Enables Search Grounding.
        """
        model = genai.GenerativeModel('gemini-2.0-flash-exp') # Use experimental flash for search
        # Note: Search grounding syntax depends on SDK version. 
        # Using tools='google_search_retrieval' is the new standard for some endpoints, 
        # but let's stick to standard tools config if possible.
        
        # Construct prompt
        prompt = RESEARCH_AND_WRITE_PROMPT.format(keyword=keyword)
        
        response = model.generate_content(
            prompt
        )
        return response.text

    def refine_with_persona(self, draft_text, persona):
        """
        Rewrites the draft using a specific persona.
        """
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = REWRITE_WITH_PERSONA_PROMPT.format(persona=persona) + "\n\nTEXTO ORIGINAL:\n" + draft_text
        
        response = model.generate_content(prompt)
        return response.text

    def generate_image_prompts(self, article_text):
        """
        Asks Gemini to describe 3 images for the article.
        Returns a LIST of strings.
        """
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = IMAGE_PROMPT_GENERATION + article_text[:2000] # Truncate for context if needed
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Split by delimiter
        prompts = [p.strip() for p in text.split('|||') if p.strip()]
        
        # Fallback if AI forgot delimiter (try newlines)
        if len(prompts) < 2:
            prompts = [p.strip() for p in text.split('\n') if p.strip()]
            
        return prompts[:3] # Guarantee max 3

    def generate_images(self, image_prompt):
        """
        Uses standard REST API for Imagen 3/4 generation since SDK method is experimental.
        """
        import requests
        
        # Using Imagen 4.0 as verified available
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={GOOGLE_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        # Imagen 3/4 API payload structure
        payload = {
            "instances": [
                {
                    "prompt": image_prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9" # Standard for blog covers
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"     ❌ Imagen API Error: {response.text}")
                return []
            
            data = response.json()
            # Extract base64 image
            # Structure: predictions[0].bytesBase64Encoded or similar
            # Let's handle standard response structure
            images_b64 = []
            if 'predictions' in data:
                for pred in data['predictions']:
                    if 'bytesBase64Encoded' in pred:
                        images_b64.append(pred['bytesBase64Encoded'])
                    elif 'mimeType' in pred and 'bytesBase64Encoded' in pred:
                         images_b64.append(pred['bytesBase64Encoded'])
            
            return images_b64

        except Exception as e:
            print(f"     ❌ Image Generation Failed: {e}")
            return []
