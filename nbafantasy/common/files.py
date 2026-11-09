import os


class Files:
    """Small file helpers shared by every step."""

    @staticmethod
    def write(path, text, private=False):
        """Write via a temp file + rename, so a crash never leaves a half-written file."""
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.write(text)
        if private:
            os.chmod(tmp, 0o600)
        os.replace(tmp, path)

    @staticmethod
    def read(path):
        with open(path) as f:
            return f.read()
