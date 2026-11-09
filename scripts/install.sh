#!/bin/bash
# One-time setup: installs packages, logs in to Google, runs once, then schedules 8:00 AM daily.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3)"
echo "Using Python: $PY"
if [ ! -f "$DIR/credentials.json" ]; then echo "Missing credentials.json. See README.md Step 1."; exit 1; fi
if grep -q "PASTE_espn_s2_HERE" "$DIR/config.json"; then echo "Add your ESPN cookies to config.json first. See README.md Step 2."; exit 1; fi
chmod 600 "$DIR/config.json" "$DIR/credentials.json"
"$PY" -m pip install --user --quiet --upgrade espn-api openpyxl google-api-python-client google-auth-oauthlib
cd "$DIR"
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
  <key>StandardOutPath</key><string>$DIR/update.log</string>
  <key>StandardErrorPath</key><string>$DIR/update.log</string>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo ""
echo "Done. It will run every day at 8:00 AM."
echo "Next: give this Python Full Disk Access (README Step 4): $PY"
