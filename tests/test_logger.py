import io
import unittest

from nbafantasy.common.logger import Logger


class LoggerTest(unittest.TestCase):
    def test_logger_writes_to_its_stream(self):
        Logger.reset()
        buf = io.StringIO()
        try:
            Logger(buf, annotate=False).warning("careful")
            self.assertIn("WARNING: careful", buf.getvalue())
            self.assertNotIn("::warning::", buf.getvalue())
        finally:
            Logger.reset()

    def test_github_actions_annotations(self):
        Logger.reset()
        buf = io.StringIO()
        try:
            log = Logger(buf, annotate=True)
            log.error("two\nlines 100%")
            log.info("plain")
            self.assertIn("::error::two%0Alines 100%25\n", buf.getvalue())
            self.assertEqual(buf.getvalue().count("::"), 2)  # only the error is annotated
        finally:
            Logger.reset()


if __name__ == "__main__":
    unittest.main()
