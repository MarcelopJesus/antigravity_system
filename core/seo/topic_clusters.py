"""Topic Cluster Engine — Manages pillar/cluster article relationships for topical authority."""
import re
from core.logger import get_logger

logger = get_logger(__name__)


def get_cluster_for_keyword(keyword, topic_clusters):
    """Find which cluster a keyword belongs to.

    Args:
        keyword: The target keyword.
        topic_clusters: List of cluster dicts from tenant config.

    Returns:
        Cluster dict if found, None otherwise.
    """
    if not topic_clusters:
        return None

    kw_lower = keyword.lower().strip()
    for cluster in topic_clusters:
        pillar_kw = cluster.get("pillar_keyword", "").lower().strip()
        if kw_lower == pillar_kw:
            return cluster

        cluster_kws = [k.lower().strip() for k in cluster.get("cluster_keywords", [])]
        if kw_lower in cluster_kws:
            return cluster

    return None


def get_cluster_links(keyword, cluster, inventory):
    """Get internal links for articles within the same cluster.

    Args:
        keyword: Current article's keyword.
        cluster: Cluster dict containing pillar and cluster keywords.
        inventory: List of existing published articles (from sheets).

    Returns:
        List of link dicts: [{"text": str, "url": str, "priority": "cluster"}]
    """
    if not cluster or not inventory:
        return []

    kw_lower = keyword.lower().strip()
    pillar_kw = cluster.get("pillar_keyword", "").lower().strip()
    cluster_kws = {k.lower().strip() for k in cluster.get("cluster_keywords", [])}
    all_cluster_kws = cluster_kws | {pillar_kw}

    links = []
    inventory_by_kw = {}
    for item in inventory:
        item_kw = item.get("keyword", "").lower().strip()
        if item_kw:
            inventory_by_kw[item_kw] = item

    for target_kw in all_cluster_kws:
        if target_kw == kw_lower:
            continue  # Don't link to self

        if target_kw in inventory_by_kw:
            article = inventory_by_kw[target_kw]
            links.append({
                "text": article.get("keyword", target_kw),
                "url": article.get("url", ""),
                "priority": "cluster",
            })

    # Always link to pillar first
    links.sort(key=lambda x: 0 if x["text"].lower() == pillar_kw else 1)

    logger.info("Cluster links for '%s': %d links (cluster: %s)",
                keyword, len(links), cluster.get("name", "unknown"))
    return links


def is_pillar_keyword(keyword, topic_clusters):
    """Check if a keyword is a pillar page keyword.

    Args:
        keyword: The target keyword.
        topic_clusters: List of cluster dicts.

    Returns:
        True if keyword is a pillar keyword.
    """
    if not topic_clusters:
        return False

    kw_lower = keyword.lower().strip()
    return any(
        c.get("pillar_keyword", "").lower().strip() == kw_lower
        for c in topic_clusters
    )


def generate_toc_html(html):
    """Generate a Table of Contents from H2 headings in the article.

    Args:
        html: Article HTML content.

    Returns:
        TOC HTML string to insert after the first H2.
    """
    headings = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.IGNORECASE | re.DOTALL)
    if len(headings) < 3:
        return ""

    toc_items = []
    for heading in headings:
        clean = re.sub(r'<[^>]+>', '', heading).strip()
        slug = re.sub(r'[^\w\s-]', '', clean.lower())
        slug = re.sub(r'[\s]+', '-', slug).strip('-')
        toc_items.append(f'<li><a href="#{slug}">{clean}</a></li>')

    toc = (
        '<nav class="toc-box">\n'
        '<p><strong>Neste artigo:</strong></p>\n'
        '<ul>\n'
        + '\n'.join(toc_items) + '\n'
        '</ul>\n'
        '</nav>'
    )
    return toc


def inject_toc(html):
    """Inject Table of Contents after the first H2 opening paragraph.

    Returns:
        HTML with TOC injected, or original HTML if not enough headings.
    """
    toc = generate_toc_html(html)
    if not toc:
        return html

    # Insert after the closing tag of the first H2's content paragraph
    first_h2_end = re.search(r'</h2>', html, re.IGNORECASE)
    if first_h2_end:
        insert_pos = first_h2_end.end()
        html = html[:insert_pos] + '\n' + toc + '\n' + html[insert_pos:]

    # Add id attributes to H2 tags for TOC anchor links
    def add_id(match):
        tag_content = match.group(1)
        clean = re.sub(r'<[^>]+>', '', tag_content).strip()
        slug = re.sub(r'[^\w\s-]', '', clean.lower())
        slug = re.sub(r'[\s]+', '-', slug).strip('-')
        return f'<h2 id="{slug}">{tag_content}</h2>'

    html = re.sub(r'<h2>([^<]*(?:<[^/h][^>]*>[^<]*)*)</h2>', add_id, html, flags=re.IGNORECASE)
    return html
