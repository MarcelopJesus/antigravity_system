import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(override=True)

GOOGLE_API_KEYS_LIST = [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()]
