import io
import os
from datetime import datetime

from .google_auth import GoogleAuth
from .sheet_check import SheetCheck
from .sheet_publish_result import SheetPublishResult
from .sync_state import SyncState
from ..common.files import Files
from ..common.logger import Logger
from ..common.retry_policy import RetryPolicy
from ..common.sync_error import SyncError


class GoogleSheetPublisher:
    """Publishes the .xlsx to one Google Sheet that keeps the same link, with safety checks:
    backs up outside edits first, recreates a deleted sheet, and stops if edit access is lost."""

    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    GSHEET = "application/vnd.google-apps.spreadsheet"
    KEEP_BACKUPS = 20
    EDIT_WARNING = "Auto-updated from ESPN every day at 7 AM and 3 PM. Edits here will be replaced."

    def __init__(self, paths, auth=None, retry=None):
        self.paths = paths
        self.auth = auth or GoogleAuth(paths)
        self.retry = retry or RetryPolicy()

    def publish(self, xlsx_path, title, interactive) -> SheetPublishResult:
        from googleapiclient.discovery import build as gbuild

        creds = self.auth.credentials(interactive)
        drive = gbuild("drive", "v3", credentials=creds, cache_discovery=False)
        state = SyncState(self.paths.state).load()
        sheet_id = Files.read(self.paths.sheet_id).strip() if os.path.exists(self.paths.sheet_id) else ""

        check = SheetCheck(ok_to_update=False)
        if sheet_id:
            check = self._check_sheet(drive, sheet_id, state)
            for w in check.warnings:
                Logger().warning(w)
            if check.ok_to_update and check.edited:
                try:
                    self._backup(drive, sheet_id)
                except Exception as e:
                    # Never wipe other people's edits without a copy.
                    raise SyncError(f"Sheet was edited since last sync but the backup failed ({e}). "
                                    f"Left the sheet unchanged so nothing is lost.")

        result = SheetPublishResult(sheet_id=sheet_id, created=False, warnings=list(check.warnings))
        if check.ok_to_update:
            res = self.retry.run("Updating Google Sheet", lambda: self._upload_update(drive, sheet_id, xlsx_path))
        else:
            res = self.retry.run("Creating Google Sheet", lambda: self._upload_create(drive, title, xlsx_path))
            result.sheet_id = res["id"]
            result.created = True
            Files.write(self.paths.sheet_id, result.sheet_id)
            result.warnings.append("A NEW Google Sheet link was created. Re-share it with your league.")

        self._protect_tabs(creds, result.sheet_id)
        # Read back the final modified time (after protections) so the next run can tell if anyone edited.
        try:
            final = drive.files().get(fileId=result.sheet_id, fields="modifiedTime").execute()
            state.data["last_modified"] = final.get("modifiedTime") or res.get("modifiedTime")
        except Exception:
            state.data["last_modified"] = res.get("modifiedTime")
        state.data["last_sync"] = datetime.now().isoformat(timespec="seconds")
        state.data["sheet_id"] = result.sheet_id
        state.save()
        return result

    # ---------------------------------------------------------------- uploads
    @classmethod
    def _upload_update(cls, drive, sheet_id, xlsx_path):
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(xlsx_path, mimetype=cls.XLSX, resumable=False)
        return drive.files().update(fileId=sheet_id, media_body=media, fields="id,modifiedTime").execute()

    @classmethod
    def _upload_create(cls, drive, title, xlsx_path):
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(xlsx_path, mimetype=cls.XLSX, resumable=False)
        return drive.files().create(body={"name": title, "mimeType": cls.GSHEET}, media_body=media,
                                    fields="id,modifiedTime").execute()

    # ---------------------------------------------------------------- safety checks
    def _check_sheet(self, drive, sheet_id, state) -> SheetCheck:
        """Look at the live Google Sheet before overwriting it."""
        from googleapiclient.errors import HttpError

        try:
            meta = self.retry.run("Reading sheet info", lambda: drive.files().get(
                fileId=sheet_id,
                fields="id,name,mimeType,trashed,modifiedTime,capabilities/canEdit,"
                       "lastModifyingUser(displayName,emailAddress,me)").execute())
        except HttpError as e:
            if getattr(e.resp, "status", None) == 404:
                return SheetCheck(False, warnings=[
                    "The Google Sheet was deleted or this script lost access to it. Making a new one."])
            raise
        if meta.get("trashed"):
            return SheetCheck(False, warnings=[
                f"The Google Sheet '{meta.get('name')}' is in the Trash. Making a new one "
                f"(restore the old one from Drive's Trash if you need it)."])
        if meta.get("mimeType") != self.GSHEET:
            return SheetCheck(False, warnings=["The saved file is no longer a Google Sheet. Making a new one."])
        if not meta.get("capabilities", {}).get("canEdit", False):
            raise SyncError("Your account can no longer edit the Google Sheet. Check its sharing settings.")

        who = meta.get("lastModifyingUser") or {}
        changed_since_sync = state.last_modified and meta.get("modifiedTime") != state.last_modified
        if changed_since_sync or not who.get("me", True):
            name = who.get("displayName") or who.get("emailAddress") or "someone"
            return SheetCheck(True, edited=True, warnings=[
                f"The Google Sheet was edited since the last sync (last change by {name}). "
                f"Those edits are saved in data/backups/ and will be replaced."])
        return SheetCheck(True)

    def _backup(self, drive, sheet_id):
        """Download the edited Google Sheet as .xlsx before it gets replaced."""
        from googleapiclient.http import MediaIoBaseDownload

        folder = self.paths.backups
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"sheet_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx")
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, drive.files().export_media(fileId=sheet_id, mimeType=self.XLSX))
        done = False
        while not done:
            _, done = dl.next_chunk()
        with open(path, "wb") as f:
            f.write(buf.getvalue())
        old = sorted(p for p in os.listdir(folder) if p.endswith(".xlsx"))
        for p in old[:-self.KEEP_BACKUPS]:
            try:
                os.remove(os.path.join(folder, p))
            except OSError:
                pass
        Logger().info(f"Backed up the edited Google Sheet to {os.path.relpath(path, self.paths.root)}")

    def _protect_tabs(self, creds, sheet_id):
        """Put a 'warning only' protection on every tab, so anyone editing gets a pop-up saying
        the sheet is auto-updated. Best effort: a failure here never fails the sync."""
        try:
            from googleapiclient.discovery import build as gbuild
            sheets = gbuild("sheets", "v4", credentials=creds, cache_discovery=False)
            info = sheets.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets(properties(sheetId),protectedRanges(protectedRangeId))").execute()
            reqs = [{"addProtectedRange": {"protectedRange": {
                        "range": {"sheetId": sh["properties"]["sheetId"]},
                        "description": self.EDIT_WARNING, "warningOnly": True}}}
                    for sh in info.get("sheets", []) if not sh.get("protectedRanges")]
            if reqs:
                sheets.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()
        except Exception as e:
            Logger().info(f"Note: could not add the edit warning to the tabs ({e}). The data still updated.")
