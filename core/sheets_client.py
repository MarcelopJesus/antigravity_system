import gspread
import os

class SheetsClient:
    def __init__(self, credentials_path='config/service_account.json'):
        # Check if credentials exist
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file found at {credentials_path}. Please place your service_account.json there.")
        
        self.gc = gspread.service_account(filename=credentials_path)

    def get_pending_rows(self, spreadsheet_id):
        """
        Reads the spreadsheet and finds rows where 'Status' (Col B) is empty.
        Returns a list of dicts: {'row_id': int, 'keyword': str}
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0) # Assume first sheet
        
        # Get all records to speed up instead of iterating row by row
        # Assuming header is row 1: Keyword, Status, Link, Date
        # Using get_all_values for raw access, or get_all_records if headers are clean.
        # Let's use get_all_values to be safe with 1-indexing.
        rows = worksheet.get_all_values()
        
        pending = []
        # Skip header (index 0)
        for i, row in enumerate(rows[1:], start=2): # 1-based index starts at 2 (since 1 is header)
            # Row structure: [Keyword, Status, Link, Date]
            # Handle cases where row might be shorter
            keyword = row[0] if len(row) > 0 else ""
            status = row[1] if len(row) > 1 else ""
            
            if keyword and not status.strip(): # If keyword exists and status is empty/whitespace
                pending.append({
                    'row_num': i,
                    'keyword': keyword
                })
        return pending

    def update_row(self, spreadsheet_id, row_num, link, status="Done"):
        """
        Updates the Status (Col B) and Link (Col C).
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        
        # Col B is 2, Col C is 3.
        worksheet.update_cell(row_num, 2, status)
        worksheet.update_cell(row_num, 3, link)

    def get_all_completed_articles(self, spreadsheet_id):
        """
        Returns a list of articles that are already published (Status=Done and has Link).
        Used for Internal Linking Strategy.
        Format: [{'keyword': 'Foo', 'url': 'https://..'}, ...]
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        rows = worksheet.get_all_values()
        
        completed = []
        for row in rows[1:]:
            keyword = row[0] if len(row) > 0 else ""
            status = row[1] if len(row) > 1 else ""
            link = row[2] if len(row) > 2 else ""
            
            # Simple check: Status is Done and Link exists
            if keyword and "Done" in status and "http" in link:
                completed.append({
                    'keyword': keyword,
                    'url': link
                })
        return completed

    def add_new_topic(self, spreadsheet_id, topic):
        """
        Appends a new topic to the end of the sheet.
        """
        sh = self.gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        worksheet.append_row([topic, "Pending", "", "Growth Idea"])

