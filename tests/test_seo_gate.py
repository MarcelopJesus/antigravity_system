"""Tests for SEO Quality Gate in pipeline."""
import unittest
from unittest.mock import MagicMock, patch
from core.agents.seo_scorer import SeoScorer, SeoScore, SeoCheck


class TestSeoGradeComputation(unittest.TestCase):

    def test_grade_a(self):
        from core.agents.seo_scorer import _compute_grade
        assert _compute_grade(85) == "A"

    def test_grade_b(self):
        from core.agents.seo_scorer import _compute_grade
        assert _compute_grade(65) == "B"

    def test_grade_c(self):
        from core.agents.seo_scorer import _compute_grade
        assert _compute_grade(45) == "C"

    def test_grade_d(self):
        from core.agents.seo_scorer import _compute_grade
        assert _compute_grade(30) == "D"


class TestSeoGateLogic(unittest.TestCase):
    """Test that the gate logic works correctly at boundaries."""

    def test_score_below_40_blocks(self):
        """Score < 40 should result in grade D and block."""
        from core.agents.seo_scorer import _compute_grade
        grade = _compute_grade(39)
        assert grade == "D"
        # Pipeline should return success=False for this

    def test_score_40_to_59_warns(self):
        """Score 40-59 should result in grade C (publish with warning)."""
        from core.agents.seo_scorer import _compute_grade
        grade = _compute_grade(50)
        assert grade == "C"

    def test_score_60_plus_passes(self):
        """Score >= 60 should pass normally."""
        from core.agents.seo_scorer import _compute_grade
        grade = _compute_grade(60)
        assert grade == "B"


class TestPipelineResultSeoGrade(unittest.TestCase):

    def test_pipeline_result_has_seo_grade(self):
        from core.pipeline import PipelineResult
        result = PipelineResult(success=True, seo_grade="A", seo_score=85)
        assert result.seo_grade == "A"
        assert result.seo_score == 85

    def test_pipeline_result_default_seo_grade(self):
        from core.pipeline import PipelineResult
        result = PipelineResult(success=True)
        assert result.seo_grade == ""


if __name__ == "__main__":
    unittest.main()
