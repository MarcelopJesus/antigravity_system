"""Dry-run helpers — save pipeline output locally instead of publishing."""
import json
import os
import re
from datetime import datetime, timezone

from core.logger import get_logger

logger = get_logger(__name__)


def load_keywords_from_file(filepath):
    """Load keywords from a local JSON file.

    Expected format: [{"keyword": "...", "row_num": 1}, ...]
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {filepath}")
    for i, item in enumerate(data):
        if 'keyword' not in item:
            raise ValueError(f"Item {i} missing 'keyword' field in {filepath}")
        item.setdefault('row_num', i + 1)
    return data


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def save_dry_run_output(company_id, keyword, pipeline_result):
    """Save article HTML and metrics JSON to output/{company_id}/.

    Args:
        company_id: Company identifier.
        keyword: The keyword that was processed.
        pipeline_result: PipelineResult dataclass instance.

    Returns:
        Tuple of (html_path, json_path).
    """
    slug = slugify(keyword)
    output_dir = os.path.join('output', company_id)
    os.makedirs(output_dir, exist_ok=True)

    html_path = os.path.join(output_dir, f'{slug}.html')
    json_path = os.path.join(output_dir, f'{slug}.json')

    # Save HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(pipeline_result.content)
    logger.info("  [DRY-RUN] Saved HTML: %s", html_path)

    # Save metrics JSON
    metrics = {
        'keyword': keyword,
        'title': pipeline_result.title,
        'meta_description': pipeline_result.meta_description,
        'search_intent': pipeline_result.search_intent,
        'keyword_variations': pipeline_result.keyword_variations,
        'lsi_keywords': pipeline_result.lsi_keywords,
        'seo_score': pipeline_result.seo_score,
        'seo_grade': pipeline_result.seo_grade,
        'seo_checks': pipeline_result.seo_checks,
        'pipeline_duration_ms': pipeline_result.total_duration_ms,
        'agent_metrics': [
            {
                'agent_name': getattr(m, 'agent_name', ''),
                'duration_ms': getattr(m, 'duration_ms', 0),
                'input_chars': getattr(m, 'input_chars', 0),
                'output_chars': getattr(m, 'output_chars', 0),
                'success': getattr(m, 'success', False),
            }
            for m in (pipeline_result.agent_metrics or [])
        ],
        'outline': pipeline_result.outline,
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    logger.info("  [DRY-RUN] Saved metrics: %s", json_path)

    return html_path, json_path
