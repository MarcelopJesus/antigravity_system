import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEYS", "").split(",")[0]
genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
