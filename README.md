# NBAFantasy26

A daily sync from an ESPN fantasy basketball league to a shared Google Sheet.

Every morning at 8:00 AM, a scheduled job on a Mac pulls the league's matchups, category stats
and rosters from ESPN, builds a styled spreadsheet, and replaces the contents of one Google Sheet.
The sheet keeps the same link, so the whole league can bookmark it. A local Excel copy is saved too.

## What's in the sheet

| Tab | Shows |
|---|---|
| **Season Totals** | Each team's record, category wins/losses, season stats, and league rank in every category |
| **Weekly Stats** | Every matchup by week with the 9 category stats and each team's rank that week (the current week shows `Live`) |
| **One tab per team** | Each team's current roster with season per-game averages, refreshed every run (your team first) |

The league uses 9-category head-to-head scoring: FG%, FT%, 3PM, REB, AST, STL, BLK, TO, PTS.

## Features

- **Hands-off:** runs daily with launchd; if the Mac is asleep at 8:00 it runs on wake.
- **Safe updates:** ESPN data is validated before anything is replaced. If someone edited the sheet, a backup is saved first. A deleted sheet is recreated automatically.
- **Loud failures:** every problem shows a Mac notification and is written to `data/update.log`.
- **Least access:** Google access is limited to files this app created. Secrets never leave your machine, and a pre-commit hook blocks them from being committed.

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3, object-oriented package (`nbafantasy/`), type-checked with Pyright |
| ESPN data | [`espn-api`](https://pypi.org/project/espn-api/) (ESPN Fantasy API, cookie login) |
| Spreadsheet | [`openpyxl`](https://pypi.org/project/openpyxl/): styling, formulas, conditional formatting |
| Google | Google Drive API v3 and Google Sheets API v4 via [`google-api-python-client`](https://pypi.org/project/google-api-python-client/); OAuth 2.0 via [`google-auth-oauthlib`](https://pypi.org/project/google-auth-oauthlib/) |
| Scheduling | macOS launchd (LaunchAgent), set up by a Bash install script |
| Notifications | macOS `osascript` |
| Environment | Project-local `.venv/`; git pre-commit hook for secrets |

## Quick start

```bash
git clone https://github.com/renkecui/NBAFantasy26.git
cd NBAFantasy26
cp config.example.json config.json   # add league ID, team name and ESPN cookies
scripts/install.sh                   # needs credentials.json from Google Cloud first
```

The full walkthrough, including the Google Cloud and ESPN cookie steps, is in **[docs/SETUP.md](docs/SETUP.md)**.

## Usage

```bash
python3 fantasy_update.py            # update now (what the 8 AM job runs)
python3 fantasy_update.py --excel    # only save the local .xlsx, skip Google
python3 fantasy_update.py --login    # sign in to Google again
scripts/uninstall.sh                 # stop the daily run
```

## Documentation

- **[Setup](docs/SETUP.md)**: installation, daily use, and troubleshooting
- **[Architecture](docs/ARCHITECTURE.md)**: flowchart, how a run works, code layout, safety checks, and design decisions

## Project layout

```
fantasy_update.py     entry point
nbafantasy/           the code
scripts/              install.sh, uninstall.sh
docs/                 SETUP.md, ARCHITECTURE.md
config.example.json   template for config.json
config.json           your league settings and ESPN cookies   (private, you create it)
credentials.json      Google OAuth client                     (private, you add it)
data/                 everything the app writes                (private)
```

`config.json`, `credentials.json` and `data/` are git-ignored and never committed.
