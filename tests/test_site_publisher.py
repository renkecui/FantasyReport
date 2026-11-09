import json
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
        os.makedirs(os.path.dirname(path), exist_ok=True)
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
        self.git(d, "init", "--quiet", "--bare", "-b", "main", self.remote)
        self.git(d, "init", "--quiet", "-b", "main", self.repo)
        for k, v in (("user.name", "Test"), ("user.email", "test@example.com"), ("core.hooksPath", "/dev/null")):
            self.git(self.repo, "config", k, v)
        self.write(os.path.join(self.repo, "web", "index.html"), "<html></html>")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "--quiet", "-m", "init")
        self.git(self.repo, "remote", "add", "origin", self.remote)
        self.git(self.repo, "push", "--quiet", "origin", "main")
        self.write_site(points=100, stamp="08:00")
        self.pub = SitePublisher(self.repo, os.path.join(self.repo, "data", "site-deploy"))

    def tearDown(self):
        self.tmp.cleanup()

    def write_site(self, points, stamp):
        self.write(os.path.join(self.site, "league.json"),
                   json.dumps({"generated_at": stamp, "points": points}))

    def remote_count(self):
        return int(self.git(self.remote, "rev-list", "--count", "main").strip())

    def remote_json(self):
        return json.loads(self.git(self.remote, "show", "main:web/league.json"))

    def test_first_publish_commits_league_json_to_main(self):
        res = self.pub.publish(self.site)
        self.assertTrue(res.changed)
        self.assertEqual(self.remote_count(), 2)
        self.assertEqual(self.remote_json()["points"], 100)
        changed = self.git(self.remote, "show", "--name-only", "--format=", "main").split()
        self.assertEqual(changed, ["web/league.json"])  # nothing else in the commit

    def test_only_a_new_timestamp_is_not_committed(self):
        self.pub.publish(self.site)
        self.write_site(points=100, stamp="09:00")
        self.assertFalse(self.pub.publish(self.site).changed)
        self.assertEqual(self.remote_count(), 2)

    def test_new_data_adds_a_commit(self):
        self.pub.publish(self.site)
        self.write_site(points=120, stamp="09:00")
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertEqual(self.remote_count(), 3)
        self.assertEqual(self.remote_json()["points"], 120)

    def test_does_not_touch_the_working_checkout(self):
        self.git(self.repo, "switch", "--quiet", "-c", "my-feature")
        self.write(os.path.join(self.repo, "web", "index.html"), "<html>work in progress</html>")
        self.pub.publish(self.site)
        self.assertEqual(self.git(self.repo, "branch", "--show-current").strip(), "my-feature")
        self.assertIn("web/index.html", self.git(self.repo, "status", "--short"))
        self.assertFalse(os.path.exists(os.path.join(self.repo, "web", "league.json")))

    def test_builds_on_commits_pushed_from_elsewhere(self):
        self.pub.publish(self.site)
        other = os.path.join(self.tmp.name, "other")
        self.git(self.tmp.name, "clone", "--quiet", self.remote, other)
        for k, v in (("user.name", "Other"), ("user.email", "other@example.com")):
            self.git(other, "config", k, v)
        self.write(os.path.join(other, "README.md"), "new")
        self.git(other, "add", ".")
        self.git(other, "commit", "--quiet", "-m", "elsewhere")
        self.git(other, "push", "--quiet", "origin", "main")
        self.write_site(points=130, stamp="10:00")
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertIn("README.md", self.git(self.remote, "ls-tree", "--name-only", "main").split())
        self.assertEqual(self.remote_json()["points"], 130)

    def test_replaces_an_old_branch_checkout(self):
        # The former gh-pages setup left a checkout of another branch in data/site-deploy.
        self.git(self.repo, "branch", "gh-pages")
        self.git(self.repo, "worktree", "add", "--quiet", self.pub.deploy_dir, "gh-pages")
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertEqual(self.remote_json()["points"], 100)

    def test_fresh_checkout_after_deleting_the_folder(self):
        self.pub.publish(self.site)
        shutil.rmtree(self.pub.deploy_dir)
        self.write_site(points=140, stamp="11:00")
        self.assertTrue(self.pub.publish(self.site).changed)
        self.assertEqual(self.remote_json()["points"], 140)

    def test_pages_url(self):
        self.git(self.repo, "remote", "set-url", "origin", "https://github.com/RenkeCui/NBAFantasy26.git")
        self.assertEqual(self.pub.pages_url(), "https://renkecui.github.io/NBAFantasy26/")
        self.git(self.repo, "remote", "set-url", "origin", "git@github.com:renkecui/NBAFantasy26.git")
        self.assertEqual(self.pub.pages_url(), "https://renkecui.github.io/NBAFantasy26/")
        self.git(self.repo, "remote", "set-url", "origin", self.remote)
        self.assertIsNone(self.pub.pages_url())


if __name__ == "__main__":
    unittest.main()
