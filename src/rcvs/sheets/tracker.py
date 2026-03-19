from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger

STATUSES = ["Not Contacted", "Contacted", "Replied", "Applied"]
SHEET_COLUMNS = ["Practice Name", "Status", "Notes", "Last Updated"]


class ContactTracker:
    """
    Manages contact tracking status via Google Sheets.

    Provides graceful fallback when credentials are not configured.
    """

    def __init__(
        self,
        credentials_path: Path | None = None,
        credentials_dict: dict | None = None,
        sheet_name: str = "VetGDP Contact Tracker"
    ) -> None:
        """
        Initialise the tracker.

        Accepts credentials as either a file path or a dict (e.g. from
        ``st.secrets``). The dict takes precedence if both are provided.

        :param credentials_path: Path to Google service account JSON
        :param credentials_dict: Service account credentials as a dict
        :param sheet_name: Name of the Google Sheet to use
        """
        self._sheet = None
        self._sheet_name = sheet_name

        has_file = credentials_path and credentials_path.exists()
        has_dict = credentials_dict is not None

        if has_dict or has_file:
            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]

                if has_dict:
                    creds = Credentials.from_service_account_info(
                        credentials_dict, scopes=scopes
                    )
                else:
                    creds = Credentials.from_service_account_file(
                        str(credentials_path), scopes=scopes
                    )

                gc = gspread.authorize(creds)

                try:
                    self._sheet = gc.open(sheet_name).sheet1
                except gspread.SpreadsheetNotFound:
                    spreadsheet = gc.create(sheet_name)
                    self._sheet = spreadsheet.sheet1
                    self._sheet.append_row(SHEET_COLUMNS)
                    logger.info("Created new Google Sheet: {}", sheet_name)

                # Ensure header row exists
                first_row = self._sheet.row_values(1)
                if first_row != SHEET_COLUMNS:
                    self._sheet.insert_row(SHEET_COLUMNS, 1)
                    logger.info("Added missing header row to sheet")

                logger.info("Connected to Google Sheet: {}", sheet_name)
            except Exception as exc:
                logger.warning("Failed to connect to Google Sheets: {}", exc)
        else:
            logger.info("No Google Sheets credentials configured — tracker disabled")

    @property
    def is_configured(self) -> bool:
        """
        Check if the tracker is connected to a Google Sheet.

        :return: True if connected
        """
        return self._sheet is not None

    def get_all_statuses(self) -> dict[str, dict]:
        """
        Get all contact statuses from the sheet.

        :return: Mapping of practice name to {status, notes, last_updated}
        """
        if not self._sheet:
            return {}

        try:
            records = self._sheet.get_all_records()
            return {
                row["Practice Name"]: {
                    "status": row.get("Status", "Not Contacted"),
                    "notes": row.get("Notes", ""),
                    "last_updated": row.get("Last Updated", ""),
                }
                for row in records
                if row.get("Practice Name")
            }
        except Exception as exc:
            logger.error("Failed to read statuses: {}", exc)
            return {}

    def update_status(
        self,
        name: str,
        status: str,
        notes: str = ""
    ) -> None:
        """
        Update the contact status for a practice.

        Creates a new row if the practice doesn't exist in the sheet.

        :param name: Practice name
        :param status: Status value (one of STATUSES)
        :param notes: Optional notes
        """
        if not self._sheet:
            return

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cell = self._sheet.find(name)
            if cell:
                row_num = cell.row
                self._sheet.update_cell(row_num, 2, status)
                self._sheet.update_cell(row_num, 3, notes)
                self._sheet.update_cell(row_num, 4, now)
            else:
                self._sheet.append_row([name, status, notes, now])

            logger.debug("Updated status for {}: {}", name, status)
        except Exception as exc:
            logger.error("Failed to update status for {}: {}", name, exc)

    def init_sheet(
        self,
        names: list[str]
    ) -> None:
        """
        Initialise the sheet with practice names (skips existing entries).

        :param names: List of practice names to add
        """
        if not self._sheet:
            return

        existing = self.get_all_statuses()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        new_rows = []
        for name in names:
            if name not in existing:
                new_rows.append([name, "Not Contacted", "", now])

        if new_rows:
            self._sheet.append_rows(new_rows)
            logger.info("Added {} new practices to tracking sheet", len(new_rows))
