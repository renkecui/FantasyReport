# Fantasy Report

Daily reports for an ESPN fantasy basketball league (9-category head-to-head), as a shared Google
Sheet and a members-only website.

Twice a day, at 8:00 AM and 5:00 PM New York time, a scheduled GitHub Actions workflow pulls
matchups, category stats and rosters from ESPN, checks them, and then:

- replaces the contents of one Google Sheet (same link every day), and
- publishes the same data to a website on GitHub Pages.

It runs on GitHub's servers, so no computer needs to be on.

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
backed up first, a failed run emails you and its log is on GitHub, Google access is
limited to files the app created, and a pre-commit hook blocks secrets from being committed.

## Quick start

```bash
git clone https://github.com/renkecui/FantasyReport.git
cd FantasyReport
# create config.json: league ID, team name, ESPN cookies (docs/SETUP.md step 3)
scripts/setup.sh                     # packages + Google login; needs credentials.json from Google Cloud
```

Then add the settings as GitHub repository secrets so the scheduled workflow can run.
Full walkthrough (Google Cloud, ESPN cookies, GitHub secrets, Worker): **[docs/SETUP.md](docs/SETUP.md)**.

## Usage

```bash
python3 fantasy_update.py              # update now from this computer (what the scheduled workflow runs)
python3 fantasy_update.py --excel      # local files only (.xlsx + data/site), publish nothing
python3 fantasy_update.py --site-only  # build and publish only the website
python3 fantasy_update.py --no-site    # skip the website this run
python3 fantasy_update.py --login      # sign in to Google again
python3 -m http.server -d data/site    # preview the website at http://localhost:8000
python3 -m unittest discover -s tests -t .   # Python tests
npm --prefix worker test               # Worker tests
```

## Layout

```
fantasy_update.py   entry point
nbafantasy/         Python package, one class per file (app, espn, stats, workbook, google_sheets, website, ...)
web/                the website: plain HTML/CSS and JS modules, one class per file, no build step
worker/             Cloudflare Worker: login, session tokens, team themes (Workers KV)
tests/              Python unit tests and a made-up sample league
scripts/            setup.sh (local setup + Google login), remove-mac-schedule.sh (old Mac schedule)
.github/workflows/  update.yml (8 AM / 5 PM update), pages.yml (deploys the website), worker.yml (deploys the Worker)
docs/               SETUP, ARCHITECTURE, TODO
```

`config.json`, `credentials.json` and `data/` are private and git-ignored.

Built with Python 3 (`espn-api`, `openpyxl`, Google Drive/Sheets APIs), GitHub Actions
(schedule) + Pages, and Cloudflare Workers. Design details: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.
