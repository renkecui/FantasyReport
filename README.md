# Fantasy Report

Daily reports for an ESPN fantasy basketball league (9-category head-to-head), as a shared Google
Sheet and a members-only website.

Twice a day, at 8:00 AM and 5:00 PM, a scheduled job on a Mac pulls matchups, category stats and rosters from
ESPN, checks them, and then:

- replaces the contents of one Google Sheet (same link every day, local Excel copy saved too), and
- publishes the same data to a website on GitHub Pages.

The same run can also happen on GitHub Actions instead, so the Mac doesn't need to be on
([setup](docs/SETUP.md#9-optional-run-on-github-instead-of-the-mac)).

| Sheet tab / web page | Shows |
|---|---|
| **Season Totals** / Season | Records, category wins/losses, season stats and league ranks |
| **Weekly Stats** / Weekly | Every matchup by week with category stats and weekly ranks |
| **One tab per team** / Teams | Each roster with per-game averages, ranks and matchup history |

**The website** has sortable, rank-colored tables that work on phones. Visitors log in first:
username = their team name, password = the league password. Each team has its own color theme,
which its member can change. Login and themes run on a small Cloudflare Worker (`worker/`). The
login keeps casual visitors out, but `league.json` itself is a public file.

**Safe by default:** ESPN data is validated before anything is replaced, a hand-edited sheet is
backed up first, failures show a Mac notification and go to `data/update.log`, Google access is
limited to files the app created, and a pre-commit hook blocks secrets from being committed.

## Quick start

```bash
git clone https://github.com/renkecui/FantasyReport.git
cd FantasyReport
cp config.example.json config.json   # league ID, team name, ESPN cookies
scripts/install.sh                   # needs credentials.json from Google Cloud first
```

Full walkthrough (Google Cloud, ESPN cookies, website, Worker): **[docs/SETUP.md](docs/SETUP.md)**.

## Usage

```bash
python3 fantasy_update.py              # update now (what the 8:00 / 17:00 job runs)
python3 fantasy_update.py --excel      # local files only (.xlsx + data/site), publish nothing
python3 fantasy_update.py --site-only  # build and publish only the website
python3 fantasy_update.py --no-site    # skip the website this run
python3 fantasy_update.py --login      # sign in to Google again
python3 -m http.server -d data/site    # preview the website at http://localhost:8000
python3 -m unittest discover -s tests -t .   # Python tests
npm --prefix worker test               # Worker tests
scripts/uninstall.sh                   # stop the daily run
```

## Layout

```
fantasy_update.py   entry point
nbafantasy/         Python package, one class per file (app, espn, stats, workbook, google_sheets, website, ...)
web/                the website: plain HTML/CSS and JS modules, one class per file, no build step
worker/             Cloudflare Worker: login, session tokens, team themes (Workers KV)
tests/              Python unit tests and a made-up sample league
scripts/            install.sh / uninstall.sh (launchd job)
docs/               SETUP, ARCHITECTURE, TODO
```

`config.json`, `credentials.json` and `data/` are private and git-ignored.

Built with Python 3 (`espn-api`, `openpyxl`, Google Drive/Sheets APIs), macOS launchd, GitHub
Actions + Pages, and Cloudflare Workers. Design details: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.
