from dataclasses import dataclass, field
from typing import List


@dataclass
class SheetPublishResult:
    """The outcome of publishing to Google Sheets: which sheet, and whether it was newly created."""
    sheet_id: str
    created: bool
    warnings: List[str] = field(default_factory=list)

    @property
    def url(self):
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"
