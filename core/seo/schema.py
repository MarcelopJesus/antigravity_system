"""Schema Markup JSON-LD generators for SEO rich snippets."""
import json
import re


def generate_article_schema(title, description, url, author_name,
                            date_published, image_url, keyword):
    """Generate JSON-LD Article schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "author": {
            "@type": "Person",
            "name": author_name
        },
        "datePublished": date_published,
        "dateModified": date_published,
        "keywords": keyword,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        }
    }
    if image_url:
        schema["image"] = image_url
    return json.dumps(schema, ensure_ascii=False, indent=2)


def generate_local_business_schema(business_name, address, phone, url,
                                    geo_lat=None, geo_lng=None):
    """Generate JSON-LD LocalBusiness schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business_name,
        "address": address,
        "telephone": phone,
        "url": url
    }
    if geo_lat and geo_lng:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": str(geo_lat),
            "longitude": str(geo_lng)
        }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def generate_faq_schema(faq_items):
    """Generate JSON-LD FAQPage schema.

    Args:
        faq_items: List of dicts with 'question' and 'answer' keys.
    """
    if not faq_items:
        return ""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"]
                }
            }
            for item in faq_items
            if item.get("question") and item.get("answer")
        ]
    }
    if not schema["mainEntity"]:
        return ""
    return json.dumps(schema, ensure_ascii=False, indent=2)


def extract_faq_from_html(html):
    """Extract FAQ items from HTML if a FAQ section exists.

    Looks for H2/H3 containing 'FAQ' or 'Perguntas Frequentes',
    then extracts Q&A pairs from subsequent content.
    """
    faq_pattern = re.search(
        r'<h[23][^>]*>.*?(?:FAQ|Perguntas\s+Frequentes|Dúvidas\s+Frequentes).*?</h[23]>',
        html, re.IGNORECASE | re.DOTALL
    )
    if not faq_pattern:
        return []

    faq_start = faq_pattern.end()
    # Find next H2 or end of content
    next_h2 = re.search(r'<h2[\s>]', html[faq_start:], re.IGNORECASE)
    faq_section = html[faq_start:faq_start + next_h2.start()] if next_h2 else html[faq_start:]

    # Extract H3 questions and following paragraph answers
    items = []
    questions = re.finditer(r'<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|$)', faq_section, re.DOTALL | re.IGNORECASE)
    for match in questions:
        question = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        answer_html = match.group(2)
        answer = re.sub(r'<[^>]+>', ' ', answer_html).strip()
        answer = re.sub(r'\s+', ' ', answer)
        if question and answer:
            items.append({"question": question, "answer": answer})

    return items


def inject_schema_into_html(html, schemas):
    """Inject schema JSON-LD into HTML for dry-run/local output only.

    For WordPress publishing, use prepare_schema_meta() instead —
    WordPress strips <script> tags from the content field.

    This function is used only for dry-run output files where
    the HTML is viewed locally, not published via REST API.
    """
    if not schemas:
        return html

    schema_scripts = []
    for schema_json in schemas:
        if schema_json:
            schema_scripts.append(
                f'<script type="application/ld+json">\n{schema_json}\n</script>'
            )

    if not schema_scripts:
        return html

    schema_block = "\n".join(schema_scripts)

    # Insert before </body> if present, otherwise append
    if '</body>' in html.lower():
        html = re.sub(
            r'(</body>)', f'{schema_block}\n\\1',
            html, count=1, flags=re.IGNORECASE
        )
    else:
        html = html + "\n" + schema_block

    return html


def prepare_schema_meta(schemas):
    """Prepare schema markup as a JSON string for WordPress meta field.

    Returns a JSON string containing all schemas, ready to be sent
    via WordPress REST API as the '_seo_schema_json_ld' meta field.

    The WordPress site needs the mu-plugin (deploy/mu-seo-schema.php)
    installed to read this meta and output it in wp_head.
    """
    if not schemas:
        return ""

    valid_schemas = [s for s in schemas if s]
    if not valid_schemas:
        return ""

    # Parse each schema JSON string and combine into an array
    parsed = []
    for s in valid_schemas:
        try:
            parsed.append(json.loads(s))
        except (json.JSONDecodeError, TypeError):
            continue

    if not parsed:
        return ""

    return json.dumps(parsed, ensure_ascii=False)


def strip_schema_from_html(html):
    """Remove any JSON-LD script tags from HTML content.

    Used to clean up articles that had schema incorrectly injected
    into the post content field.
    """
    if not html:
        return html
    # Remove <script type="application/ld+json">...</script> blocks
    cleaned = re.sub(
        r'<script\s+type=["\']application/ld\+json["\']>\s*.*?\s*</script>\s*',
        '', html, flags=re.DOTALL | re.IGNORECASE
    )
    # Also remove raw JSON-LD that WordPress rendered as text (no script tags)
    # Pattern: { "@context": "https://schema.org", ... } at the start of content
    cleaned = re.sub(
        r'^\s*\{\s*"@context"\s*:\s*"https?://schema\.org".*?\}\s*',
        '', cleaned, flags=re.DOTALL
    )
    # Clean up multiple blank lines left behind
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
