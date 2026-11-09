import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Paths:
    """Every file the app reads or writes.

    Files you provide stay in the project folder (config.json, credentials.json).
    Everything the app writes goes in data/ (git-ignored).
    """
    root: str

    # Files that older versions wrote to the project folder; migrate_legacy() moves them to data/.
    LEGACY = ("token.json", "sheet_id.txt", "sync_state.json", "The_Boys_League_Stats.xlsx", "backups")

    @property
    def data_dir(self):
        return os.path.join(self.root, "data")

    def _data(self, name):
        return os.path.join(self.data_dir, name)

    # ---- you provide these
    @property
    def config(self):
        return os.path.join(self.root, "config.json")

    @property
    def credentials(self):
        return os.path.join(self.root, "credentials.json")

    # ---- the app writes these
    @property
    def token(self):
        return self._data("token.json")

    @property
    def sheet_id(self):
        return self._data("sheet_id.txt")

    @property
    def state(self):
        return self._data("sync_state.json")

    @property
    def backups(self):
        return self._data("backups")

    @property
    def lock(self):
        return self._data(".update.lock")

    @property
    def local_xlsx(self):
        return self._data("The_Boys_League_Stats.xlsx")

    @property
    def site(self):
        """The built website: web/ files plus league.json. Preview with
        python3 -m http.server -d data/site"""
        return self._data("site")

    @property
    def site_deploy(self):
        """git worktree of the gh-pages branch, used to publish the site."""
        return self._data("site-deploy")

    # ---- part of the project
    @property
    def web(self):
        return os.path.join(self.root, "web")

    def prepare(self):
        """Create data/ and move files left in the project folder by older versions.
        Returns the names moved. Never overwrites a file already in data/."""
        os.makedirs(self.data_dir, exist_ok=True)
        moved = []
        for name in self.LEGACY:
            old, new = os.path.join(self.root, name), self._data(name)
            if os.path.exists(old) and not os.path.exists(new):
                os.replace(old, new)
                moved.append(name)
        return moved
