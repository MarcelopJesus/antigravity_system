"""Multi-Language Support — hreflang tags and language-aware content generation."""
import json
from core.logger import get_logger

logger = get_logger(__name__)

# Language configs
LANGUAGE_CONFIGS = {
    "pt-br": {
        "code": "pt-BR",
        "hreflang": "pt-br",
        "name": "Português (Brasil)",
        "serp_gl": "br",
        "serp_hl": "pt-br",
    },
    "en": {
        "code": "en",
        "hreflang": "en",
        "name": "English",
        "serp_gl": "us",
        "serp_hl": "en",
    },
    "es": {
        "code": "es",
        "hreflang": "es",
        "name": "Español",
        "serp_gl": "es",
        "serp_hl": "es",
    },
}


def generate_hreflang_tags(canonical_url, translations):
    """Generate hreflang link tags for multi-language articles.

    Args:
        canonical_url: URL of the current article.
        translations: dict mapping language code → URL.
            e.g., {"pt-br": "https://site.com/artigo", "en": "https://site.com/en/article"}

    Returns:
        HTML string with hreflang link tags.
    """
    if not translations or len(translations) < 2:
        return ""

    tags = []
    for lang, url in translations.items():
        config = LANGUAGE_CONFIGS.get(lang, {})
        hreflang = config.get("hreflang", lang)
        tags.append(f'<link rel="alternate" hreflang="{hreflang}" href="{url}" />')

    # Add x-default (usually the primary language)
    primary_url = translations.get("pt-br") or list(translations.values())[0]
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{primary_url}" />')

    return "\n".join(tags)


def generate_hreflang_schema(translations):
    """Generate schema.org language alternates for JSON-LD.

    Returns:
        List of dicts for inclusion in Article schema.
    """
    if not translations or len(translations) < 2:
        return []

    alternates = []
    for lang, url in translations.items():
        config = LANGUAGE_CONFIGS.get(lang, {})
        alternates.append({
            "@type": "WebPage",
            "url": url,
            "inLanguage": config.get("code", lang),
        })

    return alternates


def get_language_config(language_code):
    """Get configuration for a specific language.

    Args:
        language_code: Language code (e.g., "pt-br", "en", "es").

    Returns:
        Config dict, or default PT-BR config if not found.
    """
    return LANGUAGE_CONFIGS.get(language_code.lower(), LANGUAGE_CONFIGS["pt-br"])


def get_tenant_languages(tenant_config):
    """Get list of enabled languages for a tenant.

    Reads from tenant.yaml → languages field.
    Default: ["pt-br"] if not configured.

    Returns:
        List of language code strings.
    """
    languages = tenant_config.raw_config.get("languages", ["pt-br"])
    return [lang.lower() for lang in languages]
