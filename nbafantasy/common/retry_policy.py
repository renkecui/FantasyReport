import time
from typing import Callable, TypeVar

from .logger import Logger

T = TypeVar("T")


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
                Logger().info(f"{what} failed (try {n}/{self.tries}): {e}. Retrying in {self.wait * n}s...")
                self._sleep(self.wait * n)
                n += 1
