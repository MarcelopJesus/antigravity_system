"""SeoScorer — Algorithmic SEO scoring (no LLM, no BaseAgent)."""
import re
from dataclasses import dataclass, field
from core.seo.readability import readability_score_pt


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


# Authoritative domains for outbound links check
_AUTHORITATIVE_DOMAINS = {
    '.gov', '.gov.br', '.edu', '.edu.br',
    'pubmed.ncbi', 'scholar.google', 'wikipedia.org',
    'who.int', 'scielo.br', 'scielo.org',
}

# Social/CTA domains to exclude from outbound link checks
_EXCLUDED_DOMAINS = {
    'wa.me', 'whatsapp.com', 'instagram.com', 'facebook.com',
    'twitter.com', 'x.com', 'linkedin.com', 'youtube.com',
    'tiktok.com',
}

# PT-BR stop words for slug check
_STOP_WORDS_PT = {
    'de', 'do', 'da', 'dos', 'das', 'a', 'o', 'as', 'os',
    'em', 'no', 'na', 'nos', 'nas', 'para', 'com', 'por',
    'que', 'um', 'uma', 'uns', 'umas', 'e', 'ou', 'se',
}


class SeoScorer:
    """Algorithmic SEO scorer — 15 checks, 100 points total."""

    def score(self, html: str, keyword: str, meta_description: str = "", title: str = "",
              lsi_keywords: list = None, slug: str = "", entities: list = None) -> SeoScore:
        """Score an article's SEO quality.

        Args:
            html: Final article HTML.
            keyword: Target keyword.
            meta_description: Meta description text.
            title: Article title (used as fallback if no H1 in HTML).
            lsi_keywords: List of LSI keywords from analyst (for semantic coverage).
            slug: Article URL slug (for slug optimization check).
            entities: List of expected entities from analyst (for entity coverage).

        Returns:
            SeoScore with total, checks, warnings, and grade.
        """
        checks = []
        warnings = []
        kw_lower = keyword.lower().strip()
        plain_text = _strip_tags(html).strip()
        plain_lower = plain_text.lower()

        # 1. Keyword in title (12 pts)
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        h1_text = _strip_tags(h1_match.group(1)).strip() if h1_match else title
        kw_in_title = kw_lower in h1_text.lower()
        checks.append(SeoCheck(
            name="keyword_in_title",
            score=12 if kw_in_title else 0,
            max_score=12,
            passed=kw_in_title,
            detail=f"H1/title: '{h1_text[:60]}'"
        ))

        # 2. Keyword in first paragraph (8 pts)
        first_300 = plain_lower[:300]
        kw_in_first = kw_lower in first_300
        checks.append(SeoCheck(
            name="keyword_in_first_paragraph",
            score=8 if kw_in_first else 0,
            max_score=8,
            passed=kw_in_first,
            detail=f"first 300 chars checked"
        ))

        # 3. Unique H1 (8 pts)
        h1_count = len(re.findall(r'<h1[\s>]', html, re.IGNORECASE))
        h1_unique = h1_count == 1
        checks.append(SeoCheck(
            name="h1_unique",
            score=8 if h1_unique else 0,
            max_score=8,
            passed=h1_unique,
            detail=f"found {h1_count} H1 tag(s)"
        ))
        if not h1_unique:
            warnings.append(f"Expected exactly 1 H1, found {h1_count}")

        # 4. Heading hierarchy (7 pts)
        headings = re.findall(r'<(h[1-6])[\s>]', html, re.IGNORECASE)
        hierarchy_ok = _check_heading_hierarchy(headings)
        checks.append(SeoCheck(
            name="heading_hierarchy",
            score=7 if hierarchy_ok else 0,
            max_score=7,
            passed=hierarchy_ok,
            detail=f"headings: {' > '.join(headings[:10])}"
        ))

        # 5. Meta description length (8 pts) — graduated scoring
        meta_len = len(meta_description)
        if 120 <= meta_len <= 155:
            meta_score = 8   # ideal range
        elif 100 <= meta_len <= 119:
            meta_score = 5   # acceptable
        elif 156 <= meta_len <= 165:
            meta_score = 3   # marginal but not zero
        else:
            meta_score = 0   # too short (<100) or too long (>165)
        meta_ok = meta_score == 8
        checks.append(SeoCheck(
            name="meta_description_length",
            score=meta_score,
            max_score=8,
            passed=meta_ok,
            detail=f"length: {meta_len} chars (score: {meta_score}/8)"
        ))
        if not meta_ok:
            warnings.append(f"Meta description {meta_len} chars (ideal: 120-155)")

        # 6. Keyword density (10 pts)
        total_words = _word_count(plain_text)
        if total_words > 0:
            kw_words = len(kw_lower.split())
            kw_count = len(re.findall(re.escape(kw_lower), plain_lower))
            density = (kw_count * kw_words / total_words) * 100
        else:
            density = 0.0
        density_ok = 0.5 <= density <= 2.5
        checks.append(SeoCheck(
            name="keyword_density",
            score=10 if density_ok else 0,
            max_score=10,
            passed=density_ok,
            detail=f"density: {density:.1f}%"
        ))

        # 7. Internal links (7 pts)
        internal_links = re.findall(r'<a\s+href=', html, re.IGNORECASE)
        has_internal = len(internal_links) >= 2
        checks.append(SeoCheck(
            name="internal_links",
            score=7 if has_internal else 0,
            max_score=7,
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

        # 9. Word count (7 pts)
        length_ok = total_words >= 1000
        checks.append(SeoCheck(
            name="word_count",
            score=7 if length_ok else 0,
            max_score=7,
            passed=length_ok,
            detail=f"{total_words} words"
        ))
        if not length_ok:
            warnings.append(f"Only {total_words} words (minimum: 1000)")

        # 10. CTA present (3 pts)
        has_cta = 'class="cta-box"' in html
        checks.append(SeoCheck(
            name="cta_present",
            score=3 if has_cta else 0,
            max_score=3,
            passed=has_cta,
            detail="CTA box found" if has_cta else "no CTA box"
        ))

        # --- NEW CHECKS (v2) ---
        # 11. Readability score (10 pts)
        readability = readability_score_pt(plain_text)
        r_index = readability["index"]
        r_level = readability["level"]
        if r_level in ("facil", "muito_facil"):
            read_score = 10
        elif r_level == "medio":
            read_score = 5
        else:
            read_score = 0
        checks.append(SeoCheck(
            name="readability",
            score=read_score,
            max_score=10,
            passed=read_score == 10,
            detail=f"Flesch PT-BR: {r_index} ({r_level})"
        ))
        if read_score < 10:
            warnings.append(f"Readability index {r_index} ({r_level}) — target: facil (50-75)")

        # 12. Semantic coverage (5 pts)
        lsi = lsi_keywords or []
        if lsi:
            lsi_found = sum(1 for kw in lsi if kw.lower() in plain_lower)
            lsi_ratio = lsi_found / len(lsi)
            if lsi_ratio >= 0.6:
                sem_score = 5
            elif lsi_ratio >= 0.4:
                sem_score = 3
            else:
                sem_score = 0
            sem_detail = f"{lsi_found}/{len(lsi)} LSI keywords ({lsi_ratio:.0%})"
        else:
            sem_score = 0
            sem_detail = "no LSI keywords provided"
        checks.append(SeoCheck(
            name="semantic_coverage",
            score=sem_score,
            max_score=5,
            passed=sem_score == 5,
            detail=sem_detail,
        ))

        # 13. Entity coverage (3 pts)
        ents = entities or []
        if ents:
            ent_found = sum(1 for e in ents if e.lower() in plain_lower)
            ent_ratio = ent_found / len(ents)
            if ent_ratio >= 0.7:
                ent_score = 3
            elif ent_ratio >= 0.4:
                ent_score = 2
            else:
                ent_score = 0
            ent_detail = f"{ent_found}/{len(ents)} entities ({ent_ratio:.0%})"
        else:
            ent_score = 0
            ent_detail = "no entities provided"
        checks.append(SeoCheck(
            name="entity_coverage",
            score=ent_score,
            max_score=3,
            passed=ent_score == 3,
            detail=ent_detail,
        ))

        # 14. Slug optimization (5 pts)
        if slug:
            slug_lower = slug.lower()
            kw_slug = kw_lower.replace(' ', '-')
            kw_in_slug = kw_slug in slug_lower or all(
                part in slug_lower for part in kw_lower.split()
            )
            slug_parts = slug_lower.split('-')
            has_stop_words = any(p in _STOP_WORDS_PT for p in slug_parts)
            slug_short = len(slug) <= 60

            if kw_in_slug and slug_short and not has_stop_words:
                slug_score = 5
            elif kw_in_slug:
                slug_score = 3
            else:
                slug_score = 0
            slug_detail = f"'{slug[:40]}' (len={len(slug)}, kw={'yes' if kw_in_slug else 'no'}, stops={'yes' if has_stop_words else 'no'})"
        else:
            slug_score = 0
            slug_detail = "no slug provided"
        checks.append(SeoCheck(
            name="slug_optimization",
            score=slug_score,
            max_score=5,
            passed=slug_score == 5,
            detail=slug_detail,
        ))

        # 15. Outbound links (2 pts)
        all_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        authoritative_count = 0
        for href in all_hrefs:
            href_lower = href.lower()
            if any(excl in href_lower for excl in _EXCLUDED_DOMAINS):
                continue
            if any(auth in href_lower for auth in _AUTHORITATIVE_DOMAINS):
                authoritative_count += 1
        if authoritative_count >= 2:
            out_score = 2
        elif authoritative_count == 1:
            out_score = 1
        else:
            out_score = 0
        checks.append(SeoCheck(
            name="outbound_links",
            score=out_score,
            max_score=2,
            passed=out_score == 2,
            detail=f"{authoritative_count} authoritative link(s)"
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
    """Compute letter grade from total score (v2 scale)."""
    if total >= 70:
        return "A"
    elif total >= 50:
        return "B"
    elif total >= 40:
        return "C"
    else:
        return "D"
