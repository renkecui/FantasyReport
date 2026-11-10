import os
import sys
import traceback
from typing import List, Optional

from .run_options import RunOptions
from .sync_pipeline import SyncPipeline
from ..common.logger import Logger
from ..common.mac_notifier import MacNotifier
from ..common.run_lock import RunLock
from ..common.singleton import Singleton
from ..common.sync_error import SyncError
from ..config.paths import Paths


class Application(metaclass=Singleton):
    """The process: project paths, the run lock, logging and failure notifications.
    There is one per process; fantasy_update.py (and so the 8am / 5pm schedule) calls main()."""

    def __init__(self, root: Optional[str] = None):
        root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.paths = Paths(root)
        self.log = Logger()
        self.notifier = MacNotifier()

    def main(self, argv: Optional[List[str]] = None):
        options = RunOptions.from_args(sys.argv[1:] if argv is None else argv)
        try:
            moved = self.paths.prepare()
            if moved:
                self.log.info(f"Moved {', '.join(moved)} into data/.")
            with RunLock(self.paths.lock):
                SyncPipeline(self.paths, options, self.notifier).run()
        except SyncError as e:
            self.fail(str(e))
        except Exception as e:
            traceback.print_exc()
            self.fail(f"Unexpected error: {e}. See data/update.log.")

    def fail(self, message):
        self.log.error(message)
        self.notifier.notify("Fantasy Report sync failed", message)
        sys.exit(1)
