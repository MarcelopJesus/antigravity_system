import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(override=True)

GOOGLE_API_KEYS_LIST = [k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()]

# Model Configuration
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")


def load_wp_credentials(site_config):
    """
    Loads WordPress credentials from environment variables.

    Supports two modes:
    1. New (secure): credentials_env_prefix in sites.json → reads from .env
    2. Legacy: wordpress_username/wordpress_app_password directly in sites.json

    Args:
        site_config: Dict from sites.json for one company

    Returns:
        (username, app_password) tuple

    Raises:
        ValueError if credentials are missing
    """
    prefix = site_config.get('credentials_env_prefix')

    if prefix:
        # Secure mode: read from environment
        username = os.getenv(f"{prefix}_WP_USERNAME")
        password = os.getenv(f"{prefix}_WP_APP_PASSWORD")

        if not username or not password:
            raise ValueError(
                f"WordPress credentials not found in environment for prefix '{prefix}'. "
                f"Expected {prefix}_WP_USERNAME and {prefix}_WP_APP_PASSWORD in .env"
            )
        return username, password

    # Legacy mode: read directly from sites.json (backward compatible)
    username = site_config.get('wordpress_username')
    password = site_config.get('wordpress_app_password')

    if not username or not password:
        raise ValueError(
            f"WordPress credentials missing for '{site_config.get('site_name', 'unknown')}'. "
            f"Add credentials_env_prefix to sites.json or provide wordpress_username/wordpress_app_password."
        )
    return username, password
