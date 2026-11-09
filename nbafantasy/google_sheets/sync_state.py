import json

from ..common.files import Files


class SyncState:
    """sync_state.json: when the sheet was last written, so the next run can spot outside edits."""

    def __init__(self, path):
        self.path = path
        self.data = {}

    def load(self):
        try:
            self.data = json.loads(Files.read(self.path))
        except Exception:
            self.data = {}
        return self

    def save(self):
        Files.write(self.path, json.dumps(self.data, indent=2))

    @property
    def last_modified(self):
        return self.data.get("last_modified")
