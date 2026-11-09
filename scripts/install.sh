#!/bin/bash
# One-time setup: installs packages, logs in to Google, runs once, then schedules 8:00 AM daily.
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"   # project folder (this script lives in scripts/)
cd "$DIR"
mkdir -p data

SYS_PY="$(command -v python3 || true)"
if [ -z "$SYS_PY" ]; then echo "python3 not found. Install Python 3 first (https://www.python.org/downloads/)."; exit 1; fi
if [ ! -f credentials.json ]; then echo "Missing credentials.json. See README.md Step 1."; exit 1; fi
if [ ! -f config.json ]; then echo "Missing config.json. Run:  cp config.example.json config.json  then fill it in (README Step 2)."; exit 1; fi
if grep -q "PASTE_espn_s2_HERE" config.json; then echo "Add your ESPN cookies to config.json first. See README.md Step 2."; exit 1; fi
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
"$PY" -m pip install --quiet --upgrade espn-api openpyxl google-api-python-client google-auth-oauthlib

echo "Logging in to Google and running once..."
"$PY" fantasy_update.py --login

PLIST="$HOME/Library/LaunchAgents/com.renke.fantasyupdate.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" << PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.renke.fantasyupdate</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>$DIR/fantasy_update.py</string></array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$DIR/data/update.log</string>
  <key>StandardErrorPath</key><string>$DIR/data/update.log</string>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

# macOS grants Full Disk Access to the real program file, not the .venv shortcut.
REAL_PY="$("$PY" -c 'import os, sys; print(os.path.realpath(sys.executable))')"
echo ""
echo "Done. It will run every day at 8:00 AM."
echo "Next: give this Python Full Disk Access (README Step 4): $REAL_PY"
