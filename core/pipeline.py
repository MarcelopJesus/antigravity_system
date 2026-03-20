"""ArticlePipeline — Orchestrates agents in sequence with validation and metrics."""
import re
import time
from dataclasses import dataclass, field
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase
from core.agents.analyst import AnalystAgent
from core.agents.writer import WriterAgent
from core.agents.humanizer import HumanizerAgent
from core.agents.editor import EditorAgent
from core.agents.base import AgentResult
from core.seo.internal_links import inject_internal_links
from core.seo.schema import (
    generate_article_schema, generate_local_business_schema,
    generate_faq_schema, extract_faq_from_html, inject_schema_into_html,
)
from core.agents.seo_scorer import SeoScorer
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
    search_intent: str = ""
    keyword_variations: list = field(default_factory=list)
    lsi_keywords: list = field(default_factory=list)
    seo_score: int = 0
    seo_checks: list = field(default_factory=list)
    seo_grade: str = ""
    slug: str = ""
    excerpt: str = ""
    missing_link_keywords: list = field(default_factory=list)


def generate_slug(title):
    """Generate URL-friendly slug from title."""
    from core.dry_run import slugify
    return slugify(title)


def generate_excerpt(html, max_sentences=2):
    """Extract first N sentences from HTML as plain text excerpt."""
    plain = re.sub(r'<[^>]+>', ' ', html).strip()
    plain = re.sub(r'\s+', ' ', plain)
    sentences = re.split(r'(?<=[.!?])\s+', plain)
    excerpt = ' '.join(sentences[:max_sentences])
    return excerpt[:300] if excerpt else ""


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
    if 'title' not in outline_json:
        return False, "Analyst output missing required field: title"
    if 'sections' not in outline_json and 'outline' not in outline_json:
        return False, "Analyst output missing required field: sections or outline"
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


def fix_image_placement(html):
    """Ensure exactly 2 IMG_PLACEHOLDERs are correctly positioned in the HTML.

    Rules:
    - Placeholder 1: After the introduction, before the first H2
    - Placeholder 2: Before the CTA box (or before the last H2 if no CTA)
    - Never adjacent (must have at least 1 H2 section between them)

    Returns the fixed HTML.
    """
    placeholder = "<!-- IMG_PLACEHOLDER -->"

    # Remove all existing placeholders
    html = html.replace(placeholder, "")
    # Clean up any empty lines left behind
    html = re.sub(r'\n{3,}', '\n\n', html)

    # Find insertion points
    h2_positions = [m.start() for m in re.finditer(r'<h2[\s>]', html, re.IGNORECASE)]
    cta_pos = html.find('<div class="cta-box">')

    if not h2_positions:
        return html

    # Placeholder 1: Before the first H2
    pos1 = h2_positions[0]

    # Placeholder 2: Before the CTA, or before the last H2 if no CTA
    if cta_pos > 0:
        pos2 = cta_pos
    elif len(h2_positions) >= 3:
        pos2 = h2_positions[-1]
    else:
        pos2 = len(html)

    # Ensure pos2 is after pos1 and they are separated
    if pos2 <= pos1:
        pos2 = len(html)

    # Insert placeholder 2 first (higher position) to not shift pos1
    html = html[:pos2] + "\n" + placeholder + "\n\n" + html[pos2:]
    # Insert placeholder 1
    html = html[:pos1] + placeholder + "\n\n" + html[pos1:]

    return html


class ArticlePipeline:
    """Orchestrates the article generation pipeline: analyst -> writer -> humanizer -> editor."""

    def __init__(self, llm_client: LLMClient, knowledge_base: KnowledgeBase = None,
                 prompt_engine=None, kb_cache=None, tenant_config=None):
        self.llm = llm_client
        self.kb = knowledge_base
        self.prompt_engine = prompt_engine
        self.kb_cache = kb_cache
        self.tenant_config = tenant_config

        agent_kwargs = {
            "prompt_engine": prompt_engine,
            "kb_cache": kb_cache,
            "tenant_config": tenant_config,
        }

        self.analyst = AnalystAgent(llm_client, knowledge_base, **agent_kwargs)
        self.writer = WriterAgent(llm_client, knowledge_base, **agent_kwargs)
        self.humanizer = HumanizerAgent(llm_client, knowledge_base, **agent_kwargs)
        self.editor = EditorAgent(llm_client, knowledge_base, **agent_kwargs)

    def run(self, keyword, links_inventory, site_config=None) -> PipelineResult:
        """Runs the full 4-agent article pipeline.

        Args:
            keyword: Target keyword for the article.
            links_inventory: List of existing articles for internal linking.
            site_config: Site configuration dict (for schema, local SEO, etc).

        Returns:
            PipelineResult with article content, title, metrics, etc.
        """
        start = time.time()
        metrics = []

        # STEP 1: ANALYST
        logger.info("  1. Analyst Agent: Creating Strategic Outline...")
        analyst_result = self.analyst.execute({
            "keyword": keyword,
            "links_inventory": links_inventory,
            "site_config": site_config or {},
        })
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
        writer_input = dict(outline_json)
        writer_input['_site_config'] = site_config or {}
        writer_result = self.writer.execute(writer_input)
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

        # Fix image placeholder positioning (safety net)
        final_content = fix_image_placement(final_content)

        is_valid, err = validate_html_output(final_content, "Editor")
        if not is_valid:
            return PipelineResult(
                success=False,
                error=f"Editor validation failed: {err}",
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )

        # STEP 5: INTERNAL LINKS INJECTION
        links_strategy = outline_json.get('internal_links_strategy', [])
        missing_link_keywords = []
        if links_strategy:
            logger.info("  5. Internal Links: Injecting links...")
            final_content, num_links = inject_internal_links(final_content, links_strategy)
            logger.info("     Inserted %d internal links", num_links)

            # Detect links to articles that don't exist in inventory
            inventory_urls = {item.get('url', '').rstrip('/').lower() for item in links_inventory}
            for link_item in links_strategy:
                link_url = link_item.get('url', '').rstrip('/').lower()
                anchor_text = link_item.get('text', '')
                if link_url and link_url not in inventory_urls:
                    missing_link_keywords.append(anchor_text)
                    logger.info("     PRIORITY keyword detected: '%s' (article needed for linking)", anchor_text)
            if missing_link_keywords:
                logger.info("     %d priority keyword(s) need to be created for link building", len(missing_link_keywords))

        # STEP 6: SEO SCORING
        logger.info("  6. SEO Scorer: Evaluating article...")
        scorer = SeoScorer()
        seo_result = scorer.score(
            html=final_content,
            keyword=keyword,
            meta_description=outline_json.get('meta_description', ''),
            title=final_title,
        )
        logger.info("     SEO Score: %d/100 (%s)", seo_result.total, seo_result.grade)
        for check in seo_result.checks:
            check_status = "OK" if check.passed else "FAIL"
            logger.info("       %s: %s — %s", check.name, check_status, check.detail)
        for warning in seo_result.warnings:
            logger.warning("       %s", warning)

        # SEO QUALITY GATE
        if seo_result.total < 40:
            logger.error("  SEO GATE BLOCKED: Score %d (grade %s) is below minimum threshold (40).",
                         seo_result.total, seo_result.grade)
            return PipelineResult(
                success=False,
                error=f"SEO score too low: {seo_result.total}/100 (grade {seo_result.grade}). Minimum is 40.",
                title=final_title,
                seo_score=seo_result.total,
                seo_grade=seo_result.grade,
                seo_checks=[
                    {'name': c.name, 'score': c.score, 'max_score': c.max_score,
                     'passed': c.passed, 'detail': c.detail}
                    for c in seo_result.checks
                ],
                agent_metrics=metrics,
                total_duration_ms=(time.time() - start) * 1000,
            )
        if seo_result.total < 60:
            logger.warning("  SEO WARNING: Score %d (grade %s). Article will be published with warning.",
                           seo_result.total, seo_result.grade)

        # STEP 7: SCHEMA MARKUP INJECTION
        cfg = site_config or {}
        schemas = []
        article_schema = generate_article_schema(
            title=final_title,
            description=outline_json.get('meta_description', ''),
            url=cfg.get('wordpress_url', ''),
            author_name=cfg.get('author_name', ''),
            date_published=time.strftime('%Y-%m-%d'),
            image_url='',
            keyword=keyword,
        )
        schemas.append(article_schema)

        if cfg.get('business_name') and cfg.get('address'):
            lb_schema = generate_local_business_schema(
                business_name=cfg['business_name'],
                address=cfg['address'],
                phone=cfg.get('phone', ''),
                url=cfg.get('wordpress_url', ''),
                geo_lat=cfg.get('geo_lat'),
                geo_lng=cfg.get('geo_lng'),
            )
            schemas.append(lb_schema)

        faq_items = extract_faq_from_html(final_content)
        if faq_items:
            faq_schema = generate_faq_schema(faq_items)
            if faq_schema:
                schemas.append(faq_schema)
                logger.info("     FAQ schema generated with %d items", len(faq_items))

        final_content = inject_schema_into_html(final_content, schemas)
        logger.info("  7. Schema Markup: Injected %d schema(s)", len(schemas))

        total_ms = (time.time() - start) * 1000
        logger.info("  Pipeline complete in %.0fms", total_ms)

        article_slug = generate_slug(final_title)
        article_excerpt = generate_excerpt(final_content)

        return PipelineResult(
            success=True,
            title=final_title,
            content=final_content,
            outline=outline_json,
            meta_description=outline_json.get('meta_description', ''),
            agent_metrics=metrics,
            total_duration_ms=total_ms,
            search_intent=outline_json.get('search_intent', ''),
            keyword_variations=outline_json.get('keyword_variations', []),
            lsi_keywords=outline_json.get('lsi_keywords', []),
            seo_score=seo_result.total,
            seo_checks=[
                {'name': c.name, 'score': c.score, 'max_score': c.max_score,
                 'passed': c.passed, 'detail': c.detail}
                for c in seo_result.checks
            ],
            seo_grade=seo_result.grade,
            slug=article_slug,
            excerpt=article_excerpt,
            missing_link_keywords=missing_link_keywords,
        )
