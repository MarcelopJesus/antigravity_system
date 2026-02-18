"""Tests for dry-run mode (Fase 5)."""
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dry_run import load_keywords_from_file, save_dry_run_output, slugify
from core.pipeline import PipelineResult
from main import parse_args


# ---------------------------------------------------------------------------
# Unit tests: core/dry_run.py
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("ansiedade generalizada") == "ansiedade-generalizada"

    def test_accents(self):
        assert slugify("terapia não invasiva") == "terapia-nao-invasiva"

    def test_special_chars(self):
        assert slugify("O que é TRI?") == "o-que-e-tri"

    def test_multiple_spaces(self):
        assert slugify("  muitos   espaços  ") == "muitos-espacos"


class TestLoadKeywordsFromFile:
    def test_load_valid_file(self, tmp_path):
        kw_file = tmp_path / "kw.json"
        kw_file.write_text(json.dumps([
            {"keyword": "ansiedade", "row_num": 1},
            {"keyword": "depressão", "row_num": 2},
        ]))
        result = load_keywords_from_file(str(kw_file))
        assert len(result) == 2
        assert result[0]['keyword'] == "ansiedade"
        assert result[1]['row_num'] == 2

    def test_auto_assigns_row_num(self, tmp_path):
        kw_file = tmp_path / "kw.json"
        kw_file.write_text(json.dumps([
            {"keyword": "tema1"},
            {"keyword": "tema2"},
        ]))
        result = load_keywords_from_file(str(kw_file))
        assert result[0]['row_num'] == 1
        assert result[1]['row_num'] == 2

    def test_missing_keyword_field(self, tmp_path):
        kw_file = tmp_path / "bad.json"
        kw_file.write_text(json.dumps([{"topic": "oops"}]))
        with pytest.raises(ValueError, match="missing 'keyword'"):
            load_keywords_from_file(str(kw_file))

    def test_not_a_list(self, tmp_path):
        kw_file = tmp_path / "bad.json"
        kw_file.write_text(json.dumps({"keyword": "single"}))
        with pytest.raises(ValueError, match="Expected a JSON array"):
            load_keywords_from_file(str(kw_file))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_keywords_from_file("/nonexistent/path.json")


class TestSaveDryRunOutput:
    def test_saves_html_and_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = PipelineResult(
            success=True,
            title="Título do Artigo",
            content="<h1>Hello</h1><p>World</p>",
            outline={"sections": [{"title": "Intro"}]},
            meta_description="Meta desc test",
            agent_metrics=[{"agent": "analyst", "duration_ms": 1000}],
            total_duration_ms=5000,
        )
        html_path, json_path = save_dry_run_output("company1", "ansiedade generalizada", result)

        assert os.path.exists(html_path)
        assert os.path.exists(json_path)

        with open(html_path, 'r') as f:
            assert "<h1>Hello</h1>" in f.read()

        with open(json_path, 'r') as f:
            metrics = json.load(f)
        assert metrics['keyword'] == "ansiedade generalizada"
        assert metrics['title'] == "Título do Artigo"
        assert metrics['pipeline_duration_ms'] == 5000
        assert 'generated_at' in metrics

    def test_creates_output_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = PipelineResult(success=True, title="T", content="C")
        save_dry_run_output("new_company", "keyword test", result)
        assert os.path.isdir(tmp_path / "output" / "new_company")


# ---------------------------------------------------------------------------
# Unit tests: parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_no_args(self):
        args = parse_args([])
        assert args.dry_run is False
        assert args.keywords is None

    def test_dry_run_flag(self):
        args = parse_args(['--dry-run'])
        assert args.dry_run is True

    def test_keywords_flag(self):
        args = parse_args(['--dry-run', '--keywords', 'config/dry_run_keywords.json'])
        assert args.dry_run is True
        assert args.keywords == 'config/dry_run_keywords.json'

    def test_keywords_without_dry_run(self):
        args = parse_args(['--keywords', 'some_file.json'])
        assert args.dry_run is False
        assert args.keywords == 'some_file.json'


# ---------------------------------------------------------------------------
# Integration tests: main() with dry-run
# ---------------------------------------------------------------------------

class TestMainDryRun:
    """Integration tests that mock external dependencies but exercise real logic."""

    @pytest.fixture
    def work_dir(self, tmp_path):
        """Set up a temp working directory with required config files."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "sites.json").write_text(json.dumps([{
            "company_id": "test_co",
            "site_name": "Test Site",
            "spreadsheet_id": "sheet123",
            "wordpress_url": "https://test.example.com",
            "credentials_env_prefix": "TEST",
        }]))
        companies_dir = config_dir / "companies" / "test_co" / "knowledge_base"
        companies_dir.mkdir(parents=True)
        kw_file = config_dir / "dry_run_keywords.json"
        kw_file.write_text(json.dumps([
            {"keyword": "ansiedade generalizada", "row_num": 1},
        ]))
        return tmp_path

    def _make_pipeline_result(self):
        return PipelineResult(
            success=True,
            title="Artigo Sobre Ansiedade",
            content="<h1>Ansiedade</h1><p>Conteúdo do artigo.</p>",
            outline={"sections": []},
            meta_description="Descrição meta",
            agent_metrics=[],
            total_duration_ms=3000,
        )

    @patch('main.GrowthAgent')
    @patch('main.ArticlePipeline')
    @patch('main.KnowledgeBase')
    @patch('main.LLMClient')
    def test_dry_run_saves_html_not_wordpress(
        self, mock_llm_cls, mock_kb_cls, mock_pipeline_cls, mock_growth_cls, work_dir, monkeypatch
    ):
        monkeypatch.chdir(work_dir)

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = self._make_pipeline_result()
        mock_pipeline_cls.return_value = mock_pipeline

        mock_growth = MagicMock()
        mock_growth.execute.return_value = MagicMock(success=True, content=["Nova ideia"])
        mock_growth_cls.return_value = mock_growth

        from main import main
        exit_code = main(
            dry_run=True,
            keywords_file=str(work_dir / "config" / "dry_run_keywords.json"),
        )

        assert exit_code == 0

        # HTML file should exist
        html_path = work_dir / "output" / "test_co" / "ansiedade-generalizada.html"
        assert html_path.exists()
        assert "<h1>Ansiedade</h1>" in html_path.read_text()

        # JSON metrics should exist
        json_path = work_dir / "output" / "test_co" / "ansiedade-generalizada.json"
        assert json_path.exists()
        metrics = json.loads(json_path.read_text())
        assert metrics['keyword'] == "ansiedade generalizada"

    @patch('main.GrowthAgent')
    @patch('main.ArticlePipeline')
    @patch('main.KnowledgeBase')
    @patch('main.LLMClient')
    def test_dry_run_does_not_call_wordpress_or_sheets(
        self, mock_llm_cls, mock_kb_cls, mock_pipeline_cls, mock_growth_cls, work_dir, monkeypatch
    ):
        monkeypatch.chdir(work_dir)

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = self._make_pipeline_result()
        mock_pipeline_cls.return_value = mock_pipeline

        mock_growth = MagicMock()
        mock_growth.execute.return_value = MagicMock(success=True, content=[])
        mock_growth_cls.return_value = mock_growth

        with patch('main.WordPressClient') as mock_wp_cls, \
             patch('main.SheetsClient') as mock_sheets_cls:

            from main import main
            main(
                dry_run=True,
                keywords_file=str(work_dir / "config" / "dry_run_keywords.json"),
            )

            # WordPress should never be instantiated or called
            mock_wp_cls.assert_not_called()

            # SheetsClient should never be instantiated (keywords from file)
            mock_sheets_cls.assert_not_called()

    @patch('main.GrowthAgent')
    @patch('main.ArticlePipeline')
    @patch('main.KnowledgeBase')
    @patch('main.LLMClient')
    def test_dry_run_without_keywords_file_uses_sheets(
        self, mock_llm_cls, mock_kb_cls, mock_pipeline_cls, mock_growth_cls, work_dir, monkeypatch
    ):
        monkeypatch.chdir(work_dir)
        # Create service_account.json so sheets init doesn't fail
        (work_dir / "config" / "service_account.json").write_text("{}")

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = self._make_pipeline_result()
        mock_pipeline_cls.return_value = mock_pipeline

        mock_growth = MagicMock()
        mock_growth.execute.return_value = MagicMock(success=True, content=[])
        mock_growth_cls.return_value = mock_growth

        mock_sheets = MagicMock()
        mock_sheets.get_pending_rows.return_value = [
            {"keyword": "terapia tri", "row_num": 1}
        ]
        mock_sheets.get_all_completed_articles.return_value = []

        with patch('main.SheetsClient', return_value=mock_sheets):
            from main import main
            exit_code = main(dry_run=True, keywords_file=None)

        assert exit_code == 0
        # Sheets was read but update_row should NOT have been called
        mock_sheets.get_pending_rows.assert_called_once()
        mock_sheets.update_row.assert_not_called()
        mock_sheets.add_new_topic.assert_not_called()

    def test_dry_run_with_missing_keywords_file(self, work_dir, monkeypatch):
        monkeypatch.chdir(work_dir)
        from main import main
        exit_code = main(dry_run=True, keywords_file="/nonexistent/file.json")
        assert exit_code == 1
