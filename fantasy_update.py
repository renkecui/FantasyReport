#!/usr/bin/env python3
"""
NBAFantasy26: pull ESPN fantasy basketball league data and update a Google Sheet.

  python3 fantasy_update.py           # normal run (what the 8am schedule does)
  python3 fantasy_update.py --login   # sign in to Google again (first time, or if the login expired)
  python3 fantasy_update.py --excel   # only save a local .xlsx copy, skip Google

The code lives in the nbafantasy/ package (see nbafantasy/__init__.py for the module map).
See README.md for setup.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# install.sh puts the packages in .venv/. If this was started with another Python
# (e.g. a plain `python3 fantasy_update.py`), restart with the .venv one.
# This must run before anything imports a third-party package.
_VENV = os.path.join(HERE, ".venv")
_VENV_PY = os.path.join(_VENV, "bin", "python3")
if os.path.exists(_VENV_PY) and os.path.realpath(sys.prefix) != os.path.realpath(_VENV):
    os.execv(_VENV_PY, [_VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])

sys.path.insert(0, HERE)
from nbafantasy.app import main  # noqa: E402

if __name__ == "__main__":
    main(root=HERE)
