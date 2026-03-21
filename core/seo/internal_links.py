"""Internal links injection — inserts links into HTML based on Analyst strategy.

Supports cluster-aware linking: cluster links get priority over general links.
"""
import re


def inject_internal_links(html: str, links_strategy: list, max_links: int = 5,
                           cluster_links: list = None) -> tuple:
    """Inject internal links into HTML based on the Analyst's link strategy.

    Cluster links get priority over general links when available.

    For each link in the strategy (up to max_links):
    1. Searches for the anchor text in the HTML (case-insensitive)
    2. Transforms the first safe occurrence into <a href="url">anchor</a>
    3. Falls back to partial match (first 2 words) if exact match fails
    4. Skips if the text is inside an <a> tag, heading (H1-H3), or CTA

    Args:
        html: The article HTML content.
        links_strategy: List of dicts with 'text', 'url' keys.
        max_links: Maximum number of links to insert.
        cluster_links: Optional list of cluster-priority links to insert first.

    Returns:
        Tuple of (html_with_links, num_links_inserted).
    """
    if not html:
        return html, 0

    inserted = 0

    # Cluster links get priority — insert first
    if cluster_links:
        for link_item in cluster_links:
            if inserted >= max_links:
                break
            anchor = link_item.get('text', '').strip()
            url = link_item.get('url', '').strip()
            if not anchor or not url:
                continue
            new_html = _try_insert_link(html, anchor, url)
            if new_html:
                html = new_html
                inserted += 1

    if not links_strategy:
        return html, inserted

    for link_item in links_strategy:
        if inserted >= max_links:
            break

        anchor = link_item.get('text', '').strip()
        url = link_item.get('url', '').strip()

        if not anchor or not url:
            continue

        new_html = _try_insert_link(html, anchor, url)
        if new_html:
            html = new_html
            inserted += 1
        else:
            # Fallback: try first 2 words
            words = anchor.split()
            if len(words) >= 2:
                partial = ' '.join(words[:2])
                new_html = _try_insert_link(html, partial, url)
                if new_html:
                    html = new_html
                    inserted += 1

    return html, inserted


def _try_insert_link(html: str, anchor: str, url: str) -> str | None:
    """Try to insert a link for the given anchor text.

    Returns the modified HTML if successful, None otherwise.
    """
    escaped = re.escape(anchor)
    pattern = re.compile(escaped, re.IGNORECASE)

    for match in pattern.finditer(html):
        start, end = match.start(), match.end()

        if _is_inside_protected_tag(html, start, end):
            continue

        matched_text = match.group(0)
        replacement = f'<a href="{url}">{matched_text}</a>'
        return html[:start] + replacement + html[end:]

    return None


def _is_inside_protected_tag(html: str, start: int, end: int) -> bool:
    """Check if position is inside an <a>, <h1>, <h2>, <h3> tag or CTA div."""
    preceding = html[:start]

    # Check headings and anchor tags
    for tag in ('a', 'h1', 'h2', 'h3'):
        last_open = preceding.rfind(f'<{tag}')
        if last_open == -1:
            continue
        last_close = preceding.rfind(f'</{tag}>')
        if last_open > last_close:
            return True

    # Check if inside cta-box div
    last_cta_open = preceding.rfind('class="cta-box"')
    if last_cta_open != -1:
        last_cta_close = preceding.rfind('</div>', last_cta_open)
        if last_cta_close == -1:
            return True

    return False
