import os
import sys
import traceback

from .config import Config, Paths
from .errors import SyncError
from .espn_client import EspnClient
from .google_sync import GoogleAuth, GoogleSheetPublisher
from .lock import RunLock
from .util import MacNotifier, RetryPolicy, log
from .validation import LeagueValidator
from .workbook import WorkbookBuilder


class SyncApp:
    """One run: ESPN -> validate -> local .xlsx -> Google Sheet.

    args: "--login" signs in to Google again first; "--excel" skips Google.
    """

    def __init__(self, paths, args, notifier=None):
        self.paths = paths
        self.args = set(args)
        self.notifier = notifier or MacNotifier()
        self.retry = RetryPolicy()
        self.auth = GoogleAuth(paths)

    @property
    def interactive(self):
        return "--login" in self.args

    def run(self):
        config = Config.load(self.paths.config)
        if self.interactive:
            self.auth.credentials(interactive=True)
            log("Google login saved.")

        data = EspnClient(config, self.retry).fetch()
        LeagueValidator(config).validate(data)

        local = self.paths.local_xlsx
        tmp = local + ".tmp.xlsx"
        WorkbookBuilder(data).save(tmp)
        os.replace(tmp, local)  # local copy, always kept up to date
        msg = f"ESPN data OK: {len(data.weeks)} weeks, {len(data.rosters)} rosters."

        if "--excel" not in self.args:
            publisher = GoogleSheetPublisher(self.paths, self.auth, self.retry)
            result = publisher.publish(local, config.sheet_title, interactive=self.interactive)
            msg += f" {'Created' if result.created else 'Updated'} Google Sheet: {result.url}"
            if result.warnings:
                self.notifier.notify("NBAFantasy26 sync", result.warnings[-1])
        log(msg)


def main(argv=None, root=None):
    """Entry point used by fantasy_update.py (and so by the 8am schedule)."""
    argv = sys.argv[1:] if argv is None else argv
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = Paths(root)
    notifier = MacNotifier()
    try:
        moved = paths.prepare()
        if moved:
            log(f"Moved {', '.join(moved)} into data/.")
        with RunLock(paths.lock):
            SyncApp(paths, argv, notifier).run()
    except SyncError as e:
        log("ERROR: " + str(e))
        notifier.notify("NBAFantasy26 sync failed", str(e))
        sys.exit(1)
    except Exception as e:
        log(f"ERROR: unexpected problem: {e}")
        traceback.print_exc()
        notifier.notify("NBAFantasy26 sync failed", f"Unexpected error: {e}. See data/update.log.")
        sys.exit(1)
