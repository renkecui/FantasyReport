import io
import unittest

from nbafantasy.common.logger import Logger


class LoggerTest(unittest.TestCase):
    def test_logger_writes_to_its_stream(self):
        Logger.reset()
        buf = io.StringIO()
        try:
            Logger(buf).warning("careful")
            self.assertIn("WARNING: careful", buf.getvalue())
        finally:
            Logger.reset()


if __name__ == "__main__":
    unittest.main()
