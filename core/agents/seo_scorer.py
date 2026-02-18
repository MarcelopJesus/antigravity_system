"""SeoScorer — Algorithmic SEO scoring (no LLM, no BaseAgent)."""
import re
from dataclasses import dataclass, field


@dataclass
class SeoCheck:
    """Result of a single SEO check."""
    name: str
    score: int        # points earned
    max_score: int    # points possible
    passed: bool
    detail: str       # e.g. "keyword density: 1.3%"


@dataclass
class SeoScore:
    """Aggregate SEO score for an article."""
    total: int = 0
    checks: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    grade: str = "D"


def _strip_tags(html: str) -> str:
    """Remove HTML tags, returning plain text."""
    return re.sub(r'<[^>]+>', ' ', html)


def _word_count(text: str) -> int:
    """Count words in plain text."""
    return len(text.split())


class SeoScorer:
    """Algorithmic SEO scorer — 10 checks, 100 points total."""

    def score(self, html: str, keyword: str, meta_description: str = "", title: str = "") -> SeoScore:
        """Score an article's SEO quality.

        Args:
            html: Final article HTML.
            keyword: Target keyword.
            meta_description: Meta description text.
            title: Article title (used as fallback if no H1 in HTML).

        Returns:
            SeoScore with total, checks, warnings, and grade.
        """
        checks = []
        warnings = []
        kw_lower = keyword.lower().strip()
        plain_text = _strip_tags(html).strip()
        plain_lower = plain_text.lower()

        # 1. Keyword in title (15 pts)
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        h1_text = _strip_tags(h1_match.group(1)).strip() if h1_match else title
        kw_in_title = kw_lower in h1_text.lower()
        checks.append(SeoCheck(
            name="keyword_in_title",
            score=15 if kw_in_title else 0,
            max_score=15,
            passed=kw_in_title,
            detail=f"H1/title: '{h1_text[:60]}'"
        ))

        # 2. Keyword in first paragraph (10 pts)
        first_300 = plain_lower[:300]
        kw_in_first = kw_lower in first_300
        checks.append(SeoCheck(
            name="keyword_in_first_paragraph",
            score=10 if kw_in_first else 0,
            max_score=10,
            passed=kw_in_first,
            detail=f"first 300 chars checked"
        ))

        # 3. Unique H1 (10 pts)
        h1_count = len(re.findall(r'<h1[\s>]', html, re.IGNORECASE))
        h1_unique = h1_count == 1
        checks.append(SeoCheck(
            name="h1_unique",
            score=10 if h1_unique else 0,
            max_score=10,
            passed=h1_unique,
            detail=f"found {h1_count} H1 tag(s)"
        ))
        if not h1_unique:
            warnings.append(f"Expected exactly 1 H1, found {h1_count}")

        # 4. Heading hierarchy (10 pts)
        headings = re.findall(r'<(h[1-6])[\s>]', html, re.IGNORECASE)
        hierarchy_ok = _check_heading_hierarchy(headings)
        checks.append(SeoCheck(
            name="heading_hierarchy",
            score=10 if hierarchy_ok else 0,
            max_score=10,
            passed=hierarchy_ok,
            detail=f"headings: {' > '.join(headings[:10])}"
        ))

        # 5. Meta description length (10 pts)
        meta_len = len(meta_description)
        meta_ok = 120 <= meta_len <= 155
        checks.append(SeoCheck(
            name="meta_description_length",
            score=10 if meta_ok else 0,
            max_score=10,
            passed=meta_ok,
            detail=f"length: {meta_len} chars"
        ))
        if not meta_ok:
            warnings.append(f"Meta description {meta_len} chars (ideal: 120-155)")

        # 6. Keyword density (15 pts)
        total_words = _word_count(plain_text)
        if total_words > 0:
            kw_words = len(kw_lower.split())
            # Count keyword occurrences in text
            kw_count = len(re.findall(re.escape(kw_lower), plain_lower))
            density = (kw_count * kw_words / total_words) * 100
        else:
            density = 0.0
        density_ok = 0.5 <= density <= 2.5
        checks.append(SeoCheck(
            name="keyword_density",
            score=15 if density_ok else 0,
            max_score=15,
            passed=density_ok,
            detail=f"density: {density:.1f}%"
        ))

        # 7. Internal links (10 pts)
        internal_links = re.findall(r'<a\s+href=', html, re.IGNORECASE)
        # Exclude WhatsApp CTA link
        has_internal = len(internal_links) >= 2  # at least 1 beyond the CTA
        checks.append(SeoCheck(
            name="internal_links",
            score=10 if has_internal else 0,
            max_score=10,
            passed=has_internal,
            detail=f"found {len(internal_links)} link(s)"
        ))

        # 8. Images (5 pts)
        has_images = '<!-- IMG_PLACEHOLDER -->' in html or '<img' in html.lower()
        checks.append(SeoCheck(
            name="images",
            score=5 if has_images else 0,
            max_score=5,
            passed=has_images,
            detail="IMG_PLACEHOLDER or <img> found" if has_images else "no images found"
        ))

        # 9. Word count (10 pts)
        length_ok = total_words >= 1000
        checks.append(SeoCheck(
            name="word_count",
            score=10 if length_ok else 0,
            max_score=10,
            passed=length_ok,
            detail=f"{total_words} words"
        ))
        if not length_ok:
            warnings.append(f"Only {total_words} words (minimum: 1000)")

        # 10. CTA present (5 pts)
        has_cta = 'class="cta-box"' in html
        checks.append(SeoCheck(
            name="cta_present",
            score=5 if has_cta else 0,
            max_score=5,
            passed=has_cta,
            detail="CTA box found" if has_cta else "no CTA box"
        ))

        total = sum(c.score for c in checks)
        grade = _compute_grade(total)

        return SeoScore(total=total, checks=checks, warnings=warnings, grade=grade)


def _check_heading_hierarchy(headings: list) -> bool:
    """Check that headings don't skip levels (e.g. H1 -> H3 without H2)."""
    if not headings:
        return True

    levels = [int(h[1]) for h in headings]
    for i in range(1, len(levels)):
        # Allow same level or going up (smaller number) or one step down
        if levels[i] > levels[i - 1] + 1:
            return False
    return True


def _compute_grade(total: int) -> str:
    """Compute letter grade from total score."""
    if total >= 80:
        return "A"
    elif total >= 60:
        return "B"
    elif total >= 40:
        return "C"
    else:
        return "D"
