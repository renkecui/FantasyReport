# NBAFantasy26

A daily sync from an ESPN fantasy basketball league to a shared Google Sheet and a website.

Every morning at 8:00 AM, a scheduled job on a Mac pulls the league's matchups, category stats
and rosters from ESPN, builds a styled spreadsheet, and replaces the contents of one Google Sheet.
The sheet keeps the same link, so the whole league can bookmark it. A local Excel copy is saved too.
The same data is published as a website on GitHub Pages, with sortable tables that work on phones.

## What's in the sheet

| Tab | Shows |
|---|---|
| **Season Totals** | Each team's record, category wins/losses, season stats, and league rank in every category |
| **Weekly Stats** | Every matchup by week with the 9 category stats and each team's rank that week (the current week shows `Live`) |
| **One tab per team** | Each team's current roster with season per-game averages, refreshed every run (your team first) |

The league uses 9-category head-to-head scoring: FG%, FT%, 3PM, REB, AST, STL, BLK, TO, PTS.

## The website

The same three tables as pages: **Season** (standings, season stats and league ranks, with switches for
totals or per-week averages and to include or leave out the week in progress), **Weekly**
(matchup cards and each week's category breakdown) and **Teams** (each roster, category ranks and
matchup history). Columns sort with a click, cells are colored by rank, and a Stats/Ranks switch
shows values or ranks. Every team has its own color theme.

Visitors see a login screen first: the username is their team name (any capitalization) and the
password is the shared league password. "Remember me" (on by default) keeps them logged in until
the end of the season. Once logged in, the site highlights their team, and they can pick their
team's color theme from a list (a color another team has can't be picked). Login and themes run on
a small Cloudflare Worker in `worker/` ([setup](docs/SETUP.md#8-optional-turn-on-login-and-team-themes-cloudflare-worker)).
The login screen keeps casual visitors out of the pages, but `league.json` itself is still a public
file, so it isn't a way to hide the data.

It's a static site in `web/` on `main`: the daily run commits fresh data to
`web/league.json` and a GitHub Actions workflow deploys `web/` to GitHub Pages. Setup: [docs/SETUP.md](docs/SETUP.md#7-optional-publish-the-website).

## Features

- **Hands-off:** runs daily with launchd; if the Mac is asleep at 8:00 it runs on wake.
- **Safe updates:** ESPN data is validated before anything is replaced. If someone edited the sheet, a backup is saved first. A deleted sheet is recreated automatically.
- **Loud failures:** every problem shows a Mac notification and is written to `data/update.log`.
- **Least access:** Google access is limited to files this app created. Secrets never leave your machine, and a pre-commit hook blocks them from being committed.

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3, object-oriented package (`nbafantasy/`: one class per file in subpackages, singletons for the logger, notifier and app), type-checked with Pyright |
| ESPN data | [`espn-api`](https://pypi.org/project/espn-api/) (ESPN Fantasy API, cookie login) |
| Website | Plain HTML, CSS and JavaScript ES modules, one class per file (no build step) in `web/`; deployed from `main` to GitHub Pages by GitHub Actions |
| Login and themes | Cloudflare Worker + Workers KV (free plan), signed session tokens; tested with `node --test` |
| Spreadsheet | [`openpyxl`](https://pypi.org/project/openpyxl/): styling, formulas, conditional formatting |
| Google | Google Drive API v3 and Google Sheets API v4 via [`google-api-python-client`](https://pypi.org/project/google-api-python-client/); OAuth 2.0 via [`google-auth-oauthlib`](https://pypi.org/project/google-auth-oauthlib/) |
| Scheduling | macOS launchd (LaunchAgent), set up by a Bash install script |
| Notifications | macOS `osascript` |
| Environment | Project-local `.venv/`; git pre-commit hook for secrets |
| Tests | `unittest` (`python3 -m unittest discover -s tests -t .`) |

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
python3 fantasy_update.py --excel    # local files only: .xlsx + website in data/site, publish nothing
python3 fantasy_update.py --site-only  # build and publish only the website
python3 fantasy_update.py --no-site  # skip publishing the website this run
python3 -m http.server -d data/site # preview the website at http://localhost:8000
python3 fantasy_update.py --login    # sign in to Google again
scripts/uninstall.sh                 # stop the daily run
```

## Documentation

- **[Setup](docs/SETUP.md)**: installation, daily use, and troubleshooting
- **[Architecture](docs/ARCHITECTURE.md)**: flowchart, how a run works, code layout, safety checks, and design decisions
- **[Website plan](docs/WEBSITE_PLAN.md)**: planned website on GitHub Pages, plus near-live data and chat bots on free services
- **[TODO](docs/TODO.md)**: ideas and planned features

## Project layout

```
fantasy_update.py     entry point
nbafantasy/           the code: one class per file, grouped by job (app/, espn/, stats/, workbook/, website/, ...)
web/                  the website: index.html, style.css and js/ (one class per file)
worker/               Cloudflare Worker for login and team themes (npm test, npm run dev, wrangler deploy)
tests/                one unit-test file per class, and a made-up sample league
scripts/              install.sh, uninstall.sh
docs/                 SETUP.md, ARCHITECTURE.md, WEBSITE_PLAN.md, TODO.md
config.example.json   template for config.json
config.json           your league settings and ESPN cookies   (private, you create it)
credentials.json      Google OAuth client                     (private, you add it)
data/                 everything the app writes                (private)
```

`config.json`, `credentials.json` and `data/` are git-ignored and never committed.
