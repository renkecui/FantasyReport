#!/bin/bash
# Removes the old Mac schedule (a launchd job that ran the update at 8 AM / 5 PM).
# The update now runs on GitHub Actions (.github/workflows/update.yml). Safe to run more than once.
PLIST="$HOME/Library/LaunchAgents/com.renke.fantasyupdate.plist"
launchctl unload "$PLIST" 2>/dev/null
rm -f "$PLIST" "$PLIST.disabled"
echo "Mac schedule removed. Updates now run only on GitHub Actions."
