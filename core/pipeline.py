"""ArticlePipeline — Orchestrates agents in sequence with validation and metrics."""
import time
from dataclasses import dataclass, field
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase
from core.agents.analyst import AnalystAgent
from core.agents.writer import WriterAgent
from core.agents.humanizer import HumanizerAgent
from core.agents.editor import EditorAgent
from core.agents.base import AgentResult
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a full pipeline execution."""
    success: bool
    title: str = ""
    content: str = ""
    outline: dict = field(default_factory=dict)
    meta_description: str = ""
    agent_metrics: list = field(default_factory=list)
    total_duration_ms: float = 0
    error: str = ""


def validate_keyword(keyword, seen_keywords):
    """Validates a keyword before processing."""
    if not keyword or not keyword.strip():
        return False, "Keyword is empty"
    if len(keyword) > 200:
        return False, f"Keyword too long ({len(keyword)} chars, max 200)"
    if keyword.strip().lower() in seen_keywords:
        return False, f"Duplicate keyword in this batch: '{keyword}'"
    return True, ""


def validate_analyst_output(outline_json):
    """Validates the analyst agent output (JSON structure)."""
    if not isinstance(outline_json, dict):
        return False, "Analyst output is not a valid JSON object"
    required_fields = ['title', 'sections']
    missing = [f for f in required_fields if f not in outline_json]
    if missing:
        return False, f"Analyst output missing required fields: {missing}"
    if not outline_json.get('title', '').strip():
        return False, "Analyst output has empty title"
    return True, ""


def validate_html_output(html, agent_name, min_ratio=0.0, reference_len=0):
    """Validates HTML output from writer/humanizer/editor agents."""
    if not html or not html.strip():
        return False, f"{agent_name} returned empty output"
    if len(html.strip()) < 100:
        return False, f"{agent_name} output too short ({len(html)} chars)"
    if html.strip().startswith("```"):
        return False, f"{agent_name} output starts with markdown code block"
    if min_ratio > 0 and reference_len > 0:
        ratio = len(html) / reference_len
        if ratio < min_ratio:
            return False, f"{agent_name} output is only {ratio:.0%} of input (min {min_ratio:.0%})"
    return True, ""


def clean_orphan_placeholders(html):
    """Removes any remaining IMG_PLACEHOLDER tags from final HTML."""
    return html.replace("<!-- IMG_PLACEHOLDER -->", "")


class ArticlePipeline:
    """Orchestrates the article generation pipeline: analyst -> writer -> humanizer -> editor."""

    def __init__(self, llm_client: LLMClient, knowledge_base: KnowledgeBase):
        self.llm = llm_client
        self.kb = knowledge_base

        self.analyst = AnalystAgent(llm_client, knowledge_base)
        self.writer = WriterAgent(llm_client, knowledge_base)
        self.humanizer = HumanizerAgent(llm_client, knowledge_base)
        self.editor = EditorAgent(llm_client, knowledge_base)

    def run(self, keyword, links_inventory) -> PipelineResult:
        """Runs the full 4-agent article pipeline.

        Args:
            keyword: Target keyword for the article.
            links_inventory: List of existing articles for internal linking.

        Returns:
            PipelineResult with article content, title, metrics, etc.
        """
        start = time.time()
        metrics = []

        # STEP 1: ANALYST
        logger.info("  1. Analyst Agent: Creating Strategic Outline...")
        analyst_result = self.analyst.execute({"keyword": keyword, "links_inventory": links_inventory})
        metrics.append(analyst_result)

        if not analyst_result.success:
            return PipelineResult(
                success=False,
                error=f"Analyst failed: {analyst_result.error}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        outline_json = analyst_result.content
        is_valid, err = validate_analyst_output(outline_json)
        if not is_valid:
            return PipelineResult(
                success=False,
                error=f"Analyst validation failed: {err}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        final_title = outline_json.get('title', keyword.title())
        logger.info("     Title: %s", final_title)

        # STEP 2: WRITER
        logger.info("  2. Senior Writer Agent: Writing Content...")
        writer_result = self.writer.execute(outline_json)
        metrics.append(writer_result)

        if not writer_result.success:
            return PipelineResult(
                success=False,
                error=f"Writer failed: {writer_result.error}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        draft_html = writer_result.content
        is_valid, err = validate_html_output(draft_html, "Writer")
        if not is_valid:
            return PipelineResult(
                success=False,
                error=f"Writer validation failed: {err}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        # STEP 3: HUMANIZER
        logger.info("  3. Humanizer Agent: Injecting TRI Voice...")
        humanizer_result = self.humanizer.execute(draft_html)
        metrics.append(humanizer_result)

        if not humanizer_result.success:
            return PipelineResult(
                success=False,
                error=f"Humanizer failed: {humanizer_result.error}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        humanized_html = humanizer_result.content
        is_valid, err = validate_html_output(
            humanized_html, "Humanizer",
            min_ratio=0.5, reference_len=len(draft_html)
        )
        if not is_valid:
            return PipelineResult(
                success=False,
                error=f"Humanizer validation failed: {err}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        # STEP 4: EDITOR
        logger.info("  4. Editor Agent: Polishing & SEO Check...")
        editor_result = self.editor.execute(humanized_html)
        metrics.append(editor_result)

        if not editor_result.success:
            return PipelineResult(
                success=False,
                error=f"Editor failed: {editor_result.error}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        final_content = editor_result.content
        is_valid, err = validate_html_output(final_content, "Editor")
        if not is_valid:
            return PipelineResult(
                success=False,
                error=f"Editor validation failed: {err}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        total_ms = (time.time() - start) * 1000
        logger.info("  Pipeline complete in %.0fms", total_ms)

        return PipelineResult(
            success=True,
            title=final_title,
            content=final_content,
            outline=outline_json,
            meta_description=outline_json.get('meta_description', ''),
            agent_metrics=metrics,
            total_duration_ms=total_ms,
        )
