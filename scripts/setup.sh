#!/bin/bash
# Local setup, for running or developing the update by hand and for the Google login that the
# scheduled GitHub Actions run uses: installs packages in .venv/, turns on the "no secrets" commit
# check, signs in to Google and runs once. The schedule itself lives in .github/workflows/update.yml.
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"   # project folder (this script lives in scripts/)
cd "$DIR"
mkdir -p data

SYS_PY="$(command -v python3 || true)"
if [ -z "$SYS_PY" ]; then echo "python3 not found. Install Python 3 first (https://www.python.org/downloads/)."; exit 1; fi
if [ ! -f credentials.json ]; then echo "Missing credentials.json. See docs/SETUP.md step 2."; exit 1; fi
if [ ! -f config.json ]; then echo "Missing config.json. Run:  cp config.example.json config.json  then fill it in (docs/SETUP.md step 3)."; exit 1; fi
if grep -q "PASTE_espn_s2_HERE" config.json; then echo "Add your ESPN cookies to config.json first (docs/SETUP.md step 3)."; exit 1; fi
chmod 600 config.json credentials.json

# Turn on the "no secrets" commit check if this folder is a git checkout.
if git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$DIR" config core.hooksPath .githooks
fi

# Packages go in a private .venv/ folder. This works on Homebrew / newer Pythons
# that refuse "pip install --user" (externally-managed-environment).
echo "Setting up packages in .venv/ (using $SYS_PY)..."
"$SYS_PY" -m venv "$DIR/.venv"
PY="$DIR/.venv/bin/python3"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet --upgrade -r "$DIR/requirements.txt"

echo "Logging in to Google and running once..."
"$PY" fantasy_update.py --login

echo ""
echo "Done. data/token.json and data/sheet_id.txt now hold the Google login and sheet ID:"
echo "add them as GitHub secrets (docs/SETUP.md step 5) so the scheduled run can use them."
