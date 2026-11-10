import subprocess

from .logger import Logger
from .singleton import Singleton


class MacNotifier(metaclass=Singleton):
    """Shows a macOS notification so a failed scheduled run doesn't go unnoticed.
    Where osascript doesn't exist (e.g. Linux), notifications are only logged."""

    # Text is passed as arguments, not inside the script, so quotes/backslashes can't break it.
    SCRIPT = ("on run argv", "display notification (item 1 of argv) with title (item 2 of argv)", "end run")

    def notify(self, title, msg):
        cmd = ["osascript"]
        for line in self.SCRIPT:
            cmd += ["-e", line]
        try:
            subprocess.run(cmd + [str(msg)[:200], str(title)], timeout=10, capture_output=True)
        except Exception:
            Logger().info(f"[notification] {title}: {msg}")
