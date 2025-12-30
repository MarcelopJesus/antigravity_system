import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
