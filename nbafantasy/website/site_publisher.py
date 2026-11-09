import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional

from .site_publish_result import SitePublishResult
from ..common.sync_error import SyncError


class SitePublisher:
    """The day's league.json -> web/league.json on main, pushed to GitHub. A GitHub Actions
    workflow (.github/workflows/pages.yml) then deploys web/ to GitHub Pages.

    The commit is made in a separate checkout of main in data/site-deploy/ (detached, so it never
    clashes with the main checkout), so it never touches the branch or files you are working on.
    Nothing is committed when only the timestamp changed. Pushing uses the Mac's GitHub login.
    """

    BRANCH = "main"
    REMOTE = "origin"
    DATA_FILE = "league.json"
    TARGET = "web/league.json"  # where the data lives in the repository
    TIMEOUT = 120
    VOLATILE_KEYS = ("generated_at",)  # a change in only these isn't worth a commit

    def __init__(self, repo_dir, deploy_dir, runner=subprocess.run):
        self.repo_dir = repo_dir
        self.deploy_dir = deploy_dir
        self._run = runner

    # ---------------------------------------------------------------- public
    def publish(self, site_dir, message=None) -> SitePublishResult:
        """Commit and push site_dir/league.json if the league data changed."""
        message = message or f"Update league data ({datetime.now():%Y-%m-%d %H:%M})"
        source = os.path.join(site_dir, self.DATA_FILE)
        push = ["push", "--quiet", self.REMOTE, f"HEAD:refs/heads/{self.BRANCH}"]
        for last_try in (False, True):  # try again if someone else pushed to main in between
            self._prepare_checkout()
            if not self._copy_if_changed(source):
                return SitePublishResult(changed=False, url=self.pages_url())
            self._git(self.deploy_dir, "add", self.TARGET)
            self._git(self.deploy_dir, "commit", "--quiet", "-m", message, "--", self.TARGET)
            if last_try:
                self._git(self.deploy_dir, *push)  # raises with git's message if it fails again
            elif not self._ok(self.deploy_dir, *push):
                continue
            break
        return SitePublishResult(changed=True, url=self.pages_url())

    def pages_url(self) -> Optional[str]:
        """https://<owner>.github.io/<repo>/ for a GitHub remote, else None."""
        try:
            remote = self._git(self.repo_dir, "remote", "get-url", self.REMOTE).strip()
        except SyncError:
            return None
        m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote)
        return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/" if m else None

    # ---------------------------------------------------------------- internals
    def _remote_ref(self):
        return f"refs/remotes/{self.REMOTE}/{self.BRANCH}"

    def _prepare_checkout(self):
        """Make data/site-deploy a detached checkout of GitHub's main, creating it the first time
        (and replacing an old checkout of another branch, e.g. the former gh-pages)."""
        self._git(self.repo_dir, "fetch", "--quiet", self.REMOTE,
                  f"+refs/heads/{self.BRANCH}:{self._remote_ref()}")
        has_checkout = os.path.exists(os.path.join(self.deploy_dir, ".git"))
        if has_checkout and not self._is_detached():
            self._ok(self.repo_dir, "worktree", "remove", "--force", self.deploy_dir)
            has_checkout = False
        if not has_checkout:
            if os.path.exists(self.deploy_dir):
                shutil.rmtree(self.deploy_dir)
            self._git(self.repo_dir, "worktree", "prune")
            self._git(self.repo_dir, "worktree", "add", "--quiet", "--detach", self.deploy_dir, self._remote_ref())
        else:
            self._git(self.deploy_dir, "reset", "--quiet", "--hard", self._remote_ref())

    def _is_detached(self):
        res = self._call(self.deploy_dir, ["symbolic-ref", "--quiet", "HEAD"])
        return res.returncode != 0

    def _copy_if_changed(self, source) -> bool:
        """Copy the new league.json over the committed one. False if only the timestamp differs."""
        target = os.path.join(self.deploy_dir, self.TARGET)
        if os.path.exists(target) and self._content(target) == self._content(source):
            return False
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
        return True

    @classmethod
    def _content(cls, path):
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None
        if isinstance(data, dict):
            for key in cls.VOLATILE_KEYS:
                data.pop(key, None)
        return data

    def _call(self, cwd, args: List[str]):
        try:
            return self._run(["git", "-C", cwd] + list(args), capture_output=True, text=True,
                             timeout=self.TIMEOUT)
        except (OSError, subprocess.SubprocessError) as e:
            raise SyncError(f"git {args[0]} failed: {e}")

    def _ok(self, cwd, *args) -> bool:
        return self._call(cwd, list(args)).returncode == 0

    def _git(self, cwd, *args) -> str:
        res = self._call(cwd, list(args))
        if res.returncode != 0:
            detail = (res.stderr or res.stdout or "").strip().splitlines()
            raise SyncError(f"Website publish failed at 'git {' '.join(args[:2])}': "
                            f"{detail[-1] if detail else 'exit ' + str(res.returncode)}")
        return res.stdout or ""
