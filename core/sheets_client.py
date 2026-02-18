import gspread
import os
from core.logger import get_logger

logger = get_logger(__name__)


class SheetsClient:
    def __init__(self, credentials_path='config/service_account.json'):
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found at {credentials_path}. Please place your service_account.json there.")

        self.gc = gspread.service_account(filename=credentials_path)
        logger.info("Google Sheets client initialized.")

    def get_pending_rows(self, spreadsheet_id):
        """
        Reads the spreadsheet and finds rows where 'Status' (Col B) is empty
        or has PRIORIDADE flag (priority keywords for internal linking).
        Priority keywords are sorted first so they get processed before regular ones.
        Returns a list of dicts: {'row_num': int, 'keyword': str}
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        rows = worksheet.get_all_values()

        priority = []
        regular = []
        for i, row in enumerate(rows[1:], start=2):
            keyword = row[0] if len(row) > 0 else ""
            status = row[1] if len(row) > 1 else ""

            if not keyword:
                continue

            if "PRIORIDADE" in status:
                priority.append({
                    'row_num': i,
                    'keyword': keyword
                })
            elif not status.strip():
                regular.append({
                    'row_num': i,
                    'keyword': keyword
                })

        # Priority keywords first, then regular pending
        pending = priority + regular
        logger.info("Found %d pending keywords (%d priority, %d regular).",
                     len(pending), len(priority), len(regular))
        return pending

    def update_row(self, spreadsheet_id, row_num, link, status="Done"):
        """
        Updates the Status (Col B) and Link (Col C).
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        worksheet.update_cell(row_num, 2, status)
        worksheet.update_cell(row_num, 3, link)
        logger.info("Updated row %d: status='%s'", row_num, status)

    def get_all_completed_articles(self, spreadsheet_id):
        """
        Returns a list of articles that are already published (Status=Done and has Link).
        Used for Internal Linking Strategy.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        rows = worksheet.get_all_values()

        completed = []
        for row in rows[1:]:
            keyword = row[0] if len(row) > 0 else ""
            status = row[1] if len(row) > 1 else ""
            link = row[2] if len(row) > 2 else ""

            if keyword and "Done" in status and "http" in link:
                completed.append({
                    'keyword': keyword,
                    'url': link
                })
        logger.info("Found %d completed articles for internal linking.", len(completed))
        return completed

    def add_new_topic(self, spreadsheet_id, topic):
        """
        Appends a new topic suggested by AI to the end of the sheet.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        worksheet.append_row([topic, "💡 Sugestão IA", ""])
        logger.info("New topic added: %s", topic)

    def add_priority_keyword(self, spreadsheet_id, keyword, source_article=""):
        """
        Adds a keyword with PRIORITY flag — needed for internal linking.
        These keywords should be written FIRST to enable link building.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        # Check if keyword already exists in the sheet to avoid duplicates
        existing = worksheet.col_values(1)
        if keyword.strip().lower() in [k.strip().lower() for k in existing]:
            logger.info("Priority keyword '%s' already exists in sheet. Skipping.", keyword)
            return False

        worksheet.append_row([keyword, f"🔗 PRIORIDADE (link de: {source_article[:40]})", ""])
        logger.info("PRIORITY keyword added: '%s' (needed by: %s)", keyword, source_article[:40])
        return True
