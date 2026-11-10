#!/usr/bin/env python3
"""
Fantasy Report: pull ESPN fantasy basketball league data and update a Google Sheet.

  python3 fantasy_update.py           # normal run (what the scheduled GitHub Actions run does)
  python3 fantasy_update.py --login   # sign in to Google again (first time, or if the login expired)
  python3 fantasy_update.py --excel   # local files only: .xlsx + website in data/site, publish nothing
  python3 fantasy_update.py --site-only  # build and publish only the website (GitHub Pages)
  python3 fantasy_update.py --no-site    # don't publish the website this run

The code lives in the nbafantasy/ package, one class per file (see nbafantasy/__init__.py for the map).
See README.md for setup.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# scripts/setup.sh puts the packages in .venv/. If this was started with another Python
# (e.g. a plain `python3 fantasy_update.py`), restart with the .venv one.
# This must run before anything imports a third-party package.
_VENV = os.path.join(HERE, ".venv")
_VENV_PY = os.path.join(_VENV, "bin", "python3")
if os.path.exists(_VENV_PY) and os.path.realpath(sys.prefix) != os.path.realpath(_VENV):
    os.execv(_VENV_PY, [_VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])

sys.path.insert(0, HERE)
from nbafantasy.app.application import Application  # noqa: E402

if __name__ == "__main__":
    Application(root=HERE).main()
