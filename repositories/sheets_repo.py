from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from common.errors import NotFoundError

try:
    import gspread
    from gspread import Spreadsheet, Worksheet
    from gspread.exceptions import APIError, WorksheetNotFound
except ImportError as exc:  # pragma: no cover - executed only when dependency missing
    gspread = None  # type: ignore
    Spreadsheet = Worksheet = Any  # type: ignore
    WorksheetNotFound = APIError = Exception  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class SheetsRepositoryError(RuntimeError):
    """Raised when interacting with Google Sheets fails."""


CHILDREN_HEADERS: List[str] = [
    "child_id",
    "nickname",
    "age",
    "comm_level",
    "personality",
    "triggers_raw",
    "triggers",
    "interests_raw",
    "interests",
    "target_skills_raw",
    "target_skills",
    "created_at",
    "updated_at",
]

SESSIONS_HEADERS: List[str] = [
    "session_id",
    "child_id",
    "mood",
    "environment",
    "situation",
    "prompt",
    "created_at",
]


@dataclass(frozen=True)
class SheetNames:
    children: str = "children"
    sessions: str = "sessions"


def create_client(credentials_path: Path) -> "gspread.Client":
    """Create a gspread client using a service account JSON key file."""
    if gspread is None:  # pragma: no cover
        raise ImportError(
            "gspread is required to use SheetsRepository. "
            "Install it via `pip install gspread`."
        ) from _IMPORT_ERROR

    return gspread.service_account(filename=str(credentials_path))


class SheetsRepository:
    """Repository layer backed by Google Sheets."""

    def __init__(
        self,
        client: "gspread.Client",
        spreadsheet_id: str,
        *,
        sheet_names: Optional[SheetNames] = None,
    ) -> None:
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id must be provided.")

        self._client = client
        try:
            self._spreadsheet: Spreadsheet = client.open_by_key(spreadsheet_id)
        except APIError as exc:  # pragma: no cover - network call
            raise SheetsRepositoryError(
                f"Failed to open spreadsheet with id '{spreadsheet_id}'."
            ) from exc

        names = sheet_names or SheetNames()
        try:
            self._children_ws: Worksheet = self._spreadsheet.worksheet(names.children)
        except WorksheetNotFound as exc:
            raise SheetsRepositoryError(
                f"Worksheet '{names.children}' not found in spreadsheet."
            ) from exc

        try:
            self._sessions_ws: Worksheet = self._spreadsheet.worksheet(names.sessions)
        except WorksheetNotFound as exc:
            raise SheetsRepositoryError(
                f"Worksheet '{names.sessions}' not found in spreadsheet."
            ) from exc

    # --------------------------------------------------------------------- #
    # Children operations                                                   #
    # --------------------------------------------------------------------- #

    def create_child(self, record: Dict[str, Any]) -> None:
        """Append a child record to the sheet."""
        row = self._serialize_row(CHILDREN_HEADERS, record)
        self._children_ws.append_row(row, value_input_option="USER_ENTERED")

    def get_child(self, child_id: str) -> Dict[str, Any]:
        """Fetch a single child record by identifier."""
        row_index = self._find_row_by_id(self._children_ws, child_id)
        if row_index is None:
            raise NotFoundError(f"Child '{child_id}' not found.", details={"child_id": child_id})

        values = self._children_ws.row_values(row_index)
        record = self._deserialize_row(CHILDREN_HEADERS, values)
        record["age"] = int(record["age"]) if record.get("age") else None
        return record

    def update_child(self, child_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing child record."""
        row_index = self._find_row_by_id(self._children_ws, child_id)
        if row_index is None:
            raise NotFoundError(f"Child '{child_id}' not found.", details={"child_id": child_id})

        current_values = self._children_ws.row_values(row_index)
        current_record = self._deserialize_row(CHILDREN_HEADERS, current_values)
        current_record.update(updates)
        new_row = self._serialize_row(CHILDREN_HEADERS, current_record)

        cell_range = f"A{row_index}:{self._column_letter(len(CHILDREN_HEADERS))}{row_index}"
        self._children_ws.update(cell_range, [new_row])
        return current_record

    # --------------------------------------------------------------------- #
    # Session operations                                                    #
    # --------------------------------------------------------------------- #

    def create_session(self, record: Dict[str, Any]) -> None:
        """Append a session record to the sheet."""
        row = self._serialize_row(SESSIONS_HEADERS, record)
        self._sessions_ws.append_row(row, value_input_option="USER_ENTERED")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Fetch a single session record by identifier."""
        row_index = self._find_row_by_id(self._sessions_ws, session_id)
        if row_index is None:
            raise NotFoundError(
                f"Session '{session_id}' not found.", details={"session_id": session_id}
            )

        values = self._sessions_ws.row_values(row_index)
        return self._deserialize_row(SESSIONS_HEADERS, values)

    # --------------------------------------------------------------------- #
    # Helpers                                                               #
    # --------------------------------------------------------------------- #

    @staticmethod
    def _serialize_row(headers: Iterable[str], record: Dict[str, Any]) -> List[Any]:
        """Convert a record dict into an ordered row matching the headers."""
        row: List[Any] = []
        for header in headers:
            value = record.get(header, "")
            if isinstance(value, datetime):
                row.append(value.isoformat())
            else:
                row.append("" if value is None else str(value))
        return row

    @staticmethod
    def _deserialize_row(headers: List[str], row_values: List[str]) -> Dict[str, Any]:
        """Convert a row list into a dict keyed by headers."""
        values = row_values + [""] * (len(headers) - len(row_values))
        return {header: values[idx] for idx, header in enumerate(headers)}

    @staticmethod
    def _find_row_by_id(worksheet: Worksheet, identifier: str) -> Optional[int]:
        """Locate the row index for a given record ID (assumes ID is in first column)."""
        column_values = worksheet.col_values(1)
        for idx, value in enumerate(column_values, start=1):
            if value == identifier:
                return idx
        return None

    @staticmethod
    def _column_letter(index: int) -> str:
        """Return the Excel-style column letter for a 1-based index."""
        result = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result
