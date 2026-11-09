import os

from ..common.files import Files
from ..common.logger import Logger
from ..common.sync_error import SyncError


class GoogleAuth:
    """Loads, refreshes or (interactively) creates the saved Google login in token.json."""

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]  # only files this app creates

    def __init__(self, paths):
        self.paths = paths

    def credentials(self, interactive):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        token = self.paths.token
        creds = None
        if os.path.exists(token):
            try:
                creds = Credentials.from_authorized_user_file(token, self.SCOPES)
            except Exception as e:
                Logger().info(f"token.json could not be read ({e}).")
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                Files.write(token, creds.to_json(), private=True)
                return creds
            except Exception as e:
                Logger().info(f"Google login refresh failed: {e}")
        if not interactive:
            raise SyncError("Google login missing or expired. In Terminal run:  python3 fantasy_update.py --login")
        if not os.path.exists(self.paths.credentials):
            raise SyncError("credentials.json not found. See README.md step 1.")
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(self.paths.credentials, self.SCOPES).run_local_server(port=0)
        Files.write(token, creds.to_json(), private=True)
        return creds
