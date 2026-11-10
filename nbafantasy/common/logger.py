import os
import sys
from datetime import datetime
from typing import TextIO

from .singleton import Singleton


class Logger(metaclass=Singleton):
    """The one log for the whole run, on stdout (the GitHub Actions run log).
    On GitHub Actions, warnings and errors are also shown as annotations on the run's summary page."""

    def __init__(self, stream: TextIO = sys.stdout, annotate: bool = os.environ.get("GITHUB_ACTIONS") == "true"):
        self.stream = stream
        self.annotate = annotate

    def info(self, msg):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}", file=self.stream, flush=True)

    def warning(self, msg):
        self.info("WARNING: " + str(msg))
        self._annotation("warning", msg)

    def error(self, msg):
        self.info("ERROR: " + str(msg))
        self._annotation("error", msg)

    def _annotation(self, level, msg):
        if self.annotate:
            text = str(msg).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::{level}::{text}", file=self.stream, flush=True)
