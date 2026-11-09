import sys
from datetime import datetime
from typing import TextIO

from .singleton import Singleton


class Logger(metaclass=Singleton):
    """The one log for the whole run. launchd sends stdout to data/update.log."""

    def __init__(self, stream: TextIO = sys.stdout):
        self.stream = stream

    def info(self, msg):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}", file=self.stream, flush=True)

    def warning(self, msg):
        self.info("WARNING: " + str(msg))

    def error(self, msg):
        self.info("ERROR: " + str(msg))
