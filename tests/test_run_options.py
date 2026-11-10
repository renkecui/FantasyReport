import unittest

from nbafantasy.app.run_options import RunOptions
from nbafantasy.config.config import Config


class RunOptionsTest(unittest.TestCase):
    def opts(self, *args):
        return RunOptions.from_args(list(args))

    def test_publish_site(self):
        on = Config(league_id=1, publish_site=True)
        off = Config(league_id=1)
        self.assertTrue(self.opts().publish_site(on))
        self.assertFalse(self.opts().publish_site(off))
        self.assertTrue(self.opts("--site-only").publish_site(off))
        self.assertFalse(self.opts("--excel").publish_site(on))
        self.assertFalse(self.opts("--no-site").publish_site(on))
        self.assertFalse(self.opts("--site-only", "--no-site").publish_site(on))

    def test_sheet_and_workbook(self):
        self.assertTrue(self.opts().publish_sheet and self.opts().build_workbook)
        self.assertFalse(self.opts("--excel").publish_sheet)
        self.assertTrue(self.opts("--excel").build_workbook)
        self.assertFalse(self.opts("--site-only").publish_sheet)
        self.assertFalse(self.opts("--site-only").build_workbook)


if __name__ == "__main__":
    unittest.main()
