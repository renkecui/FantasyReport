#!/bin/bash
# Stops the daily update.
PLIST="$HOME/Library/LaunchAgents/com.renke.fantasyupdate.plist"
launchctl unload "$PLIST" 2>/dev/null; mv "$PLIST" "$PLIST.disabled" 2>/dev/null
echo "Daily update stopped."
