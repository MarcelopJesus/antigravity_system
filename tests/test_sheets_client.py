"""Tests for SheetsClient (Story 1.7)."""
import pytest
from unittest.mock import patch, MagicMock


class TestGetPendingRows:
    def test_returns_pending_keywords(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["Keyword", "Status", "Link", "Date"],  # Header
            ["terapia tri", "", "", ""],               # Pending
            ["ansiedade", "Done", "http://link", ""],  # Done
            ["depressão", "", "", ""],                  # Pending
        ]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet

        with patch("core.sheets_client.gspread") as mock_gspread:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            mock_gspread.service_account.return_value = mock_gc

            from core.sheets_client import SheetsClient
            with patch("os.path.exists", return_value=True):
                client = SheetsClient()
            result = client.get_pending_rows("test_id")

        assert len(result) == 2
        assert result[0]["keyword"] == "terapia tri"
        assert result[0]["row_num"] == 2
        assert result[1]["keyword"] == "depressão"
        assert result[1]["row_num"] == 4

    def test_returns_empty_for_all_done(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["Keyword", "Status", "Link"],
            ["word1", "Done", "http://link1"],
            ["word2", "Done", "http://link2"],
        ]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet

        with patch("core.sheets_client.gspread") as mock_gspread:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            mock_gspread.service_account.return_value = mock_gc

            from core.sheets_client import SheetsClient
            with patch("os.path.exists", return_value=True):
                client = SheetsClient()
            result = client.get_pending_rows("test_id")

        assert len(result) == 0

    def test_skips_empty_keyword_rows(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["Keyword", "Status"],
            ["", ""],  # Empty keyword
            ["valid", ""],  # Valid pending
        ]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet

        with patch("core.sheets_client.gspread") as mock_gspread:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            mock_gspread.service_account.return_value = mock_gc

            from core.sheets_client import SheetsClient
            with patch("os.path.exists", return_value=True):
                client = SheetsClient()
            result = client.get_pending_rows("test_id")

        assert len(result) == 1
        assert result[0]["keyword"] == "valid"


class TestGetAllCompleted:
    def test_returns_completed_articles(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["Keyword", "Status", "Link"],
            ["word1", "Done", "http://link1.com"],
            ["word2", "", ""],
            ["word3", "Done", "http://link3.com"],
        ]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet

        with patch("core.sheets_client.gspread") as mock_gspread:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            mock_gspread.service_account.return_value = mock_gc

            from core.sheets_client import SheetsClient
            with patch("os.path.exists", return_value=True):
                client = SheetsClient()
            result = client.get_all_completed_articles("test_id")

        assert len(result) == 2
        assert result[0]["keyword"] == "word1"
        assert result[0]["url"] == "http://link1.com"


class TestUpdateRow:
    def test_updates_status_and_link(self):
        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet

        with patch("core.sheets_client.gspread") as mock_gspread:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            mock_gspread.service_account.return_value = mock_gc

            from core.sheets_client import SheetsClient
            with patch("os.path.exists", return_value=True):
                client = SheetsClient()
            client.update_row("test_id", 5, "http://new-link.com", status="Done")

        mock_worksheet.update_cell.assert_any_call(5, 2, "Done")
        mock_worksheet.update_cell.assert_any_call(5, 3, "http://new-link.com")
