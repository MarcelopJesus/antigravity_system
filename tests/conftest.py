import sys
import os
import pytest

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy env vars so settings.py doesn't fail on import
os.environ.setdefault("GOOGLE_API_KEYS", "test-key-1,test-key-2")
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-test")
os.environ.setdefault("LOG_LEVEL", "WARNING")
