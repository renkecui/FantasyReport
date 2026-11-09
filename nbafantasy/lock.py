import os
import time

from .errors import SyncError
from .util import read_file


class RunLock:
    """Stops two updates from running at the same time (e.g. 8am run + manual run)."""

    MAX_AGE = 6 * 60 * 60  # a lock older than this is treated as stale even if its PID is in use

    def __init__(self, path):
        self.path = path

    def _holder_alive(self):
        """True if the lock file belongs to a process that is still running."""
        try:
            pid = int(read_file(self.path).strip())
            if time.time() - os.path.getmtime(self.path) > self.MAX_AGE:
                return False
            os.kill(pid, 0)  # signal 0 only checks that the process exists
            return True
        except PermissionError:
            return True  # exists, owned by another user
        except (OSError, ValueError):
            return False  # no lock, unreadable lock, or process is gone

    def __enter__(self):
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                if self._holder_alive():
                    raise SyncError("Another update is already running. Try again in a few minutes.")
                try:
                    os.remove(self.path)  # left behind by a run that crashed
                except OSError:
                    pass
                continue
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
            return self
        raise SyncError("Could not create the lock file data/.update.lock. Delete it and try again.")

    def __exit__(self, *exc):
        try:
            os.remove(self.path)
        except OSError:
            pass
