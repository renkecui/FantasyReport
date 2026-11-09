"""Publishes the .xlsx to one Google Sheet that keeps the same link, with safety checks."""
import io
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .errors import SyncError
from .util import RetryPolicy, log, read_file, write_file

SCOPES = ["https://www.googleapis.com/auth/drive.file"]  # only files this app creates
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
GSHEET = "application/vnd.google-apps.spreadsheet"


class GoogleAuth:
    """Loads, refreshes or (interactively) creates the saved Google login in token.json."""

    def __init__(self, paths):
        self.paths = paths

    def credentials(self, interactive):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        token = self.paths.token
        creds = None
        if os.path.exists(token):
            try:
                creds = Credentials.from_authorized_user_file(token, SCOPES)
            except Exception as e:
                log(f"token.json could not be read ({e}).")
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                write_file(token, creds.to_json(), private=True)
                return creds
            except Exception as e:
                log(f"Google login refresh failed: {e}")
        if not interactive:
            raise SyncError("Google login missing or expired. In Terminal run:  python3 fantasy_update.py --login")
        if not os.path.exists(self.paths.credentials):
            raise SyncError("credentials.json not found. See README.md step 1.")
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(self.paths.credentials, SCOPES).run_local_server(port=0)
        write_file(token, creds.to_json(), private=True)
        return creds


class SyncState:
    """sync_state.json: when the sheet was last written, so the next run can spot outside edits."""

    def __init__(self, path):
        self.path = path
        self.data = {}

    def load(self):
        try:
            self.data = json.loads(read_file(self.path))
        except Exception:
            self.data = {}
        return self

    def save(self):
        write_file(self.path, json.dumps(self.data, indent=2))

    @property
    def last_modified(self):
        return self.data.get("last_modified")


@dataclass
class PublishResult:
    sheet_id: str
    created: bool
    warnings: List[str] = field(default_factory=list)

    @property
    def url(self):
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"


@dataclass
class _SheetCheck:
    ok_to_update: bool  # False means: make a new sheet instead
    edited: bool = False
    warnings: List[str] = field(default_factory=list)


class GoogleSheetPublisher:
    KEEP_BACKUPS = 20
    EDIT_WARNING = "Auto-updated from ESPN every day at 8 AM. Edits here will be replaced."

    def __init__(self, paths, auth=None, retry=None):
        self.paths = paths
        self.auth = auth or GoogleAuth(paths)
        self.retry = retry or RetryPolicy()

    def publish(self, xlsx_path, title, interactive) -> PublishResult:
        from googleapiclient.discovery import build as gbuild

        creds = self.auth.credentials(interactive)
        drive = gbuild("drive", "v3", credentials=creds, cache_discovery=False)
        state = SyncState(self.paths.state).load()
        sheet_id = read_file(self.paths.sheet_id).strip() if os.path.exists(self.paths.sheet_id) else ""

        check = _SheetCheck(ok_to_update=False)
        if sheet_id:
            check = self._check_sheet(drive, sheet_id, state)
            for w in check.warnings:
                log("WARNING: " + w)
            if check.ok_to_update and check.edited:
                try:
                    self._backup(drive, sheet_id)
                except Exception as e:
                    # Never wipe other people's edits without a copy.
                    raise SyncError(f"Sheet was edited since last sync but the backup failed ({e}). "
                                    f"Left the sheet unchanged so nothing is lost.")

        result = PublishResult(sheet_id=sheet_id, created=False, warnings=list(check.warnings))
        if check.ok_to_update:
            res = self.retry.run("Updating Google Sheet", lambda: self._upload_update(drive, sheet_id, xlsx_path))
        else:
            res = self.retry.run("Creating Google Sheet", lambda: self._upload_create(drive, title, xlsx_path))
            result.sheet_id = res["id"]
            result.created = True
            write_file(self.paths.sheet_id, result.sheet_id)
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
    @staticmethod
    def _upload_update(drive, sheet_id, xlsx_path):
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(xlsx_path, mimetype=XLSX, resumable=False)
        return drive.files().update(fileId=sheet_id, media_body=media, fields="id,modifiedTime").execute()

    @staticmethod
    def _upload_create(drive, title, xlsx_path):
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(xlsx_path, mimetype=XLSX, resumable=False)
        return drive.files().create(body={"name": title, "mimeType": GSHEET}, media_body=media,
                                    fields="id,modifiedTime").execute()

    # ---------------------------------------------------------------- safety checks
    def _check_sheet(self, drive, sheet_id, state) -> _SheetCheck:
        """Look at the live Google Sheet before overwriting it."""
        from googleapiclient.errors import HttpError

        try:
            meta = self.retry.run("Reading sheet info", lambda: drive.files().get(
                fileId=sheet_id,
                fields="id,name,mimeType,trashed,modifiedTime,capabilities/canEdit,"
                       "lastModifyingUser(displayName,emailAddress,me)").execute())
        except HttpError as e:
            if getattr(e.resp, "status", None) == 404:
                return _SheetCheck(False, warnings=[
                    "The Google Sheet was deleted or this script lost access to it. Making a new one."])
            raise
        if meta.get("trashed"):
            return _SheetCheck(False, warnings=[
                f"The Google Sheet '{meta.get('name')}' is in the Trash. Making a new one "
                f"(restore the old one from Drive's Trash if you need it)."])
        if meta.get("mimeType") != GSHEET:
            return _SheetCheck(False, warnings=["The saved file is no longer a Google Sheet. Making a new one."])
        if not meta.get("capabilities", {}).get("canEdit", False):
            raise SyncError("Your account can no longer edit the Google Sheet. Check its sharing settings.")

        who = meta.get("lastModifyingUser") or {}
        changed_since_sync = state.last_modified and meta.get("modifiedTime") != state.last_modified
        if changed_since_sync or not who.get("me", True):
            name = who.get("displayName") or who.get("emailAddress") or "someone"
            return _SheetCheck(True, edited=True, warnings=[
                f"The Google Sheet was edited since the last sync (last change by {name}). "
                f"Those edits are saved in data/backups/ and will be replaced."])
        return _SheetCheck(True)

    def _backup(self, drive, sheet_id):
        """Download the edited Google Sheet as .xlsx before it gets replaced."""
        from googleapiclient.http import MediaIoBaseDownload

        folder = self.paths.backups
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"sheet_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx")
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, drive.files().export_media(fileId=sheet_id, mimeType=XLSX))
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
        log(f"Backed up the edited Google Sheet to {os.path.relpath(path, self.paths.root)}")

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
            log(f"Note: could not add the edit warning to the tabs ({e}). The data still updated.")
