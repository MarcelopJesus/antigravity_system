"""E-E-A-T Enhancer — Injects Experience, Expertise, Authoritativeness, Trust signals."""
import json
from core.logger import get_logger

logger = get_logger(__name__)


def generate_author_schema(author_name, credentials="", linkedin_url="", lattes_url="",
                            website_url="", image_url=""):
    """Generate schema.org/Person JSON-LD for the article author.

    Enhances Article schema with author authority signals (sameAs links).
    """
    schema = {
        "@type": "Person",
        "name": author_name,
    }

    if credentials:
        schema["jobTitle"] = credentials

    same_as = []
    if linkedin_url:
        same_as.append(linkedin_url)
    if lattes_url:
        same_as.append(lattes_url)
    if website_url:
        same_as.append(website_url)

    if same_as:
        schema["sameAs"] = same_as

    if image_url:
        schema["image"] = image_url

    return schema


def generate_reviewed_by_html(author_name, credentials=""):
    """Generate a 'Reviewed by' badge HTML for article credibility.

    Returns:
        HTML string with author badge, or empty string if no author.
    """
    if not author_name:
        return ""

    credential_text = f" — {credentials}" if credentials else ""

    return (
        f'<div class="author-badge">\n'
        f'  <p><strong>Revisado por:</strong> {author_name}{credential_text}</p>\n'
        f'</div>'
    )


def enhance_article_schema_with_author(article_schema_json, author_data):
    """Enhance an existing Article schema JSON with detailed author info.

    Args:
        article_schema_json: JSON string of the Article schema.
        author_data: dict with author details (from tenant config).

    Returns:
        Enhanced JSON string.
    """
    try:
        schema = json.loads(article_schema_json)
    except (json.JSONDecodeError, TypeError):
        return article_schema_json

    author_name = author_data.get("name", "")
    if not author_name:
        return article_schema_json

    author_schema = generate_author_schema(
        author_name=author_name,
        credentials=author_data.get("credentials", ""),
        linkedin_url=author_data.get("linkedin_url", ""),
        lattes_url=author_data.get("lattes_url", ""),
        website_url=author_data.get("website_url", ""),
    )

    schema["author"] = author_schema

    return json.dumps(schema, ensure_ascii=False, indent=2)


def inject_author_badge(html, author_name, credentials=""):
    """Inject author badge before the CTA box.

    Returns:
        HTML with author badge injected.
    """
    badge = generate_reviewed_by_html(author_name, credentials)
    if not badge:
        return html

    # Insert before CTA box if present
    if '<div class="cta-box">' in html:
        html = html.replace(
            '<div class="cta-box">',
            badge + '\n<div class="cta-box">'
        )
    else:
        html += '\n' + badge

    return html
