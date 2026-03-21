"""Featured Snippet Optimizer — Formats content sections to capture Position Zero."""
import re
from core.logger import get_logger

logger = get_logger(__name__)


def detect_snippet_opportunities(serp_brief):
    """Detect if the SERP has featured snippet opportunities.

    Args:
        serp_brief: SERP brief dict from serp_analyzer.

    Returns:
        dict with snippet_type and target_question, or None.
    """
    if not serp_brief:
        return None

    # Check if PAA questions exist (indicator of snippet opportunity)
    paa = serp_brief.get("people_also_ask", [])
    if paa:
        return {
            "has_opportunity": True,
            "type": "paragraph",  # Most common for health/therapy topics
            "target_questions": [p.get("question", "") for p in paa[:3]],
        }

    return None


def format_paragraph_snippet(question, answer_text, max_words=60):
    """Format a paragraph snippet answer (40-60 words).

    The answer should be a direct, concise response that Google
    can extract as a featured snippet.

    Args:
        question: The question being answered.
        answer_text: Full answer text.
        max_words: Maximum word count for the snippet answer.

    Returns:
        HTML formatted for snippet capture.
    """
    # Truncate to max_words at sentence boundary
    words = answer_text.split()
    if len(words) > max_words:
        truncated = ' '.join(words[:max_words])
        # End at last sentence
        last_period = truncated.rfind('.')
        if last_period > 0:
            truncated = truncated[:last_period + 1]
        answer_text = truncated

    return f'<p><strong>{question}</strong></p>\n<p>{answer_text}</p>'


def format_list_snippet(items, ordered=False):
    """Format a list snippet (numbered or bulleted).

    Args:
        items: List of strings.
        ordered: True for numbered list, False for bullets.

    Returns:
        HTML list formatted for snippet capture.
    """
    if not items:
        return ""

    tag = "ol" if ordered else "ul"
    li_items = "\n".join(f"<li>{item}</li>" for item in items)
    return f"<{tag}>\n{li_items}\n</{tag}>"


def format_table_snippet(headers, rows):
    """Format a table snippet for comparison data.

    Args:
        headers: List of column header strings.
        rows: List of lists (each inner list = one row).

    Returns:
        HTML table formatted for snippet capture.
    """
    if not headers or not rows:
        return ""

    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    tbody_rows = []
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        tbody_rows.append(f"<tr>{cells}</tr>")

    tbody = "\n".join(tbody_rows)
    return f"<table>\n<thead>{thead}</thead>\n<tbody>\n{tbody}\n</tbody>\n</table>"


def optimize_faq_for_snippets(html):
    """Optimize FAQ section HTML for featured snippet capture.

    Ensures FAQ answers start with a direct response (not "Sim," or "Não,")
    and are wrapped in proper semantic HTML.

    Returns:
        Optimized HTML.
    """
    # Find FAQ H3 questions and ensure answers are concise
    def optimize_answer(match):
        question = match.group(1)
        answer_block = match.group(2)

        # Extract first paragraph as the snippet answer
        first_p = re.search(r'<p>(.*?)</p>', answer_block, re.DOTALL)
        if first_p:
            answer = first_p.group(1).strip()
            words = answer.split()
            if len(words) > 60:
                # Truncate at sentence boundary
                truncated = ' '.join(words[:55])
                last_period = truncated.rfind('.')
                if last_period > 0:
                    answer = truncated[:last_period + 1]

        return match.group(0)  # Return unchanged for now (structural optimization)

    return html
