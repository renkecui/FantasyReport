import os
import shutil
import subprocess
import tempfile
import unittest

from nbafantasy.website.site_publisher import SitePublisher


class SitePublisherTest(unittest.TestCase):
    """Uses real git with a local bare repository standing in for GitHub."""

    @staticmethod
    def write(path, text):
        with open(path, "w") as f:
            f.write(text)

    @staticmethod
    def git(cwd, *args):
        return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True).stdout

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.remote = os.path.join(d, "remote.git")
        self.repo = os.path.join(d, "repo")
        self.site = os.path.join(d, "site")
        self.git(d, "init", "--quiet", "--bare", self.remote)
        self.git(d, "init", "--quiet", "-b", "main", self.repo)
        for k, v in (("user.name", "Test"), ("user.email", "test@example.com"), ("core.hooksPath", "/dev/null")):
            self.git(self.repo, "config", k, v)
        self.write(os.path.join(self.repo, "README.md"), "main branch\n")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "--quiet", "-m", "init")
        self.git(self.repo, "remote", "add", "origin", self.remote)
        os.makedirs(self.site)
        self.write_site("v1")
        self.pub = SitePublisher(self.repo, os.path.join(self.repo, "data", "site-deploy"))

    def tearDown(self):
        self.tmp.cleanup()

    def write_site(self, version):
        self.write(os.path.join(self.site, "index.html"), "<html></html>")
        self.write(os.path.join(self.site, "league.json"), f'{{"v": "{version}"}}')

    def remote_files(self):
        return sorted(self.git(self.remote, "ls-tree", "--name-only", "gh-pages").split())

    def test_first_publish_creates_orphan_branch(self):
        res = self.pub.publish(self.site)
        self.assertTrue(res.changed)
        self.assertEqual(self.remote_files(), [".nojekyll", "index.html", "league.json"])
        self.assertEqual(self.git(self.remote, "rev-list", "--count", "gh-pages").strip(), "1")
        self.assertNotIn("README.md", self.remote_files())  # no main-branch files

    def test_unchanged_site_is_not_pushed_again(self):
        self.pub.publish(self.site)
        before = self.git(self.remote, "rev-parse", "gh-pages")
        self.assertFalse(self.pub.publish(self.site).changed)
        self.assertEqual(self.git(self.remote, "rev-parse", "gh-pages"), before)

    def test_updates_amend_the_single_commit(self):
        self.pub.publish(self.site)
        self.write_site("v2")
        os.remove(os.path.join(self.site, "index.html"))
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertEqual(self.git(self.remote, "rev-list", "--count", "gh-pages").strip(), "1")
        self.assertEqual(self.remote_files(), [".nojekyll", "league.json"])
        self.assertIn("v2", self.git(self.remote, "show", "gh-pages:league.json"))

    def test_fresh_worktree_reuses_existing_remote_branch(self):
        self.pub.publish(self.site)
        shutil.rmtree(self.pub.deploy_dir)
        self.write_site("v3")
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertIn("v3", self.git(self.remote, "show", "gh-pages:league.json"))

    def test_pages_url(self):
        self.git(self.repo, "remote", "set-url", "origin", "https://github.com/RenkeCui/NBAFantasy26.git")
        self.assertEqual(self.pub.pages_url(), "https://renkecui.github.io/NBAFantasy26/")
        self.git(self.repo, "remote", "set-url", "origin", "git@github.com:renkecui/NBAFantasy26.git")
        self.assertEqual(self.pub.pages_url(), "https://renkecui.github.io/NBAFantasy26/")
        self.git(self.repo, "remote", "set-url", "origin", self.remote)
        self.assertIsNone(self.pub.pages_url())


if __name__ == "__main__":
    unittest.main()
