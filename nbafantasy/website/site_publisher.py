import os
import re
import shutil
import subprocess
from typing import List, Optional

from .site_publish_result import SitePublishResult
from ..common.sync_error import SyncError


class SitePublisher:
    """The built site folder -> the gh-pages branch on GitHub, served by GitHub Pages.

    Keeps a git worktree of the gh-pages branch in data/site-deploy/, replaces its files with the
    new site, and pushes. The branch holds a single commit that is amended each run, so daily
    updates don't pile up history. Pushing uses the Mac's existing GitHub login.
    """

    BRANCH = "gh-pages"
    REMOTE = "origin"
    TIMEOUT = 120

    def __init__(self, repo_dir, deploy_dir, runner=subprocess.run):
        self.repo_dir = repo_dir
        self.deploy_dir = deploy_dir
        self._run = runner

    # ---------------------------------------------------------------- public
    def publish(self, site_dir, message="Update site data") -> SitePublishResult:
        self._prepare_worktree()
        self._replace_files(site_dir)
        self._git(self.deploy_dir, "add", "-A")
        if self._ok(self.deploy_dir, "diff", "--cached", "--quiet"):
            return SitePublishResult(changed=False, url=self.pages_url())
        if self._ok(self.deploy_dir, "rev-parse", "--verify", "--quiet", "HEAD"):
            self._git(self.deploy_dir, "commit", "--quiet", "--amend", "-m", message)
        else:
            self._git(self.deploy_dir, "commit", "--quiet", "-m", message)
        self._git(self.deploy_dir, "push", "--quiet", "--force-with-lease", self.REMOTE, self.BRANCH)
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

    def _prepare_worktree(self):
        """Make data/site-deploy a checkout of gh-pages that matches GitHub's copy, creating
        the branch (with no history) the first time."""
        # Fetch failing just means the branch isn't on GitHub yet.
        self._ok(self.repo_dir, "fetch", "--quiet", self.REMOTE,
                 f"+refs/heads/{self.BRANCH}:{self._remote_ref()}")
        on_remote = self._ok(self.repo_dir, "rev-parse", "--verify", "--quiet", self._remote_ref())

        if not os.path.exists(os.path.join(self.deploy_dir, ".git")):
            if os.path.exists(self.deploy_dir):
                shutil.rmtree(self.deploy_dir)
            self._git(self.repo_dir, "worktree", "prune")
            if on_remote:
                self._git(self.repo_dir, "worktree", "add", "--quiet", "-B", self.BRANCH,
                          self.deploy_dir, self._remote_ref())
            elif self._ok(self.repo_dir, "rev-parse", "--verify", "--quiet", f"refs/heads/{self.BRANCH}"):
                self._git(self.repo_dir, "worktree", "add", "--quiet", self.deploy_dir, self.BRANCH)
            else:
                self._git(self.repo_dir, "worktree", "add", "--quiet", "--orphan", "-b", self.BRANCH,
                          self.deploy_dir)
        elif on_remote:
            self._git(self.deploy_dir, "reset", "--quiet", "--hard", self._remote_ref())

    def _replace_files(self, site_dir):
        for name in os.listdir(self.deploy_dir):
            if name == ".git":
                continue
            path = os.path.join(self.deploy_dir, name)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        for name in os.listdir(site_dir):
            src = os.path.join(site_dir, name)
            dst = os.path.join(self.deploy_dir, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        # Serve files as they are (no Jekyll processing).
        with open(os.path.join(self.deploy_dir, ".nojekyll"), "w"):
            pass

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
