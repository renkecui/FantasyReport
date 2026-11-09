import os
import subprocess
import time
from datetime import datetime
from typing import Callable, TypeVar

T = TypeVar("T")


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}", flush=True)


def write_file(path, text, private=False):
    """Write via a temp file + rename, so a crash never leaves a half-written file."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    if private:
        os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def read_file(path):
    with open(path) as f:
        return f.read()


class RetryPolicy:
    """Runs a call again after temporary errors (network, Google 429/5xx/rate limits)."""

    PERMANENT_STATUS = (400, 401, 403, 404)
    PERMANENT_ERRORS = ("ESPNAccessDenied", "ESPNInvalidLeague")

    def __init__(self, tries=3, wait=5, sleep=time.sleep):
        self.tries, self.wait, self._sleep = tries, wait, sleep

    @classmethod
    def is_permanent(cls, e):
        status = getattr(getattr(e, "resp", None), "status", None)
        if status == 403 and "ratelimitexceeded" in str(e).lower():
            return False  # Google reports rate limits as 403; those clear up on retry
        return status in cls.PERMANENT_STATUS or type(e).__name__ in cls.PERMANENT_ERRORS

    def run(self, what: str, fn: Callable[[], T]) -> T:
        """Returns fn()'s result, or raises its last error."""
        n = 1
        while True:
            try:
                return fn()
            except Exception as e:
                if self.is_permanent(e) or n >= self.tries:
                    raise
                log(f"{what} failed (try {n}/{self.tries}): {e}. Retrying in {self.wait * n}s...")
                self._sleep(self.wait * n)
                n += 1


class MacNotifier:
    """Shows a macOS notification so a failed 8am run doesn't go unnoticed."""

    # Text is passed as arguments, not inside the script, so quotes/backslashes can't break it.
    SCRIPT = ("on run argv", "display notification (item 1 of argv) with title (item 2 of argv)", "end run")

    def notify(self, title, msg):
        cmd = ["osascript"]
        for line in self.SCRIPT:
            cmd += ["-e", line]
        try:
            subprocess.run(cmd + [str(msg)[:200], str(title)], timeout=10, capture_output=True)
        except Exception:
            pass
