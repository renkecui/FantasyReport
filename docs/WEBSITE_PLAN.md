# Website plan

Goal (from [TODO](TODO.md)): show every table from the Google Sheet on a webpage the league can
bookmark, and leave room for the later **Charts** and **General Manager** ideas.

## Approach: a static site built by the existing daily job

The 8:00 AM run already fetches and validates everything. Add one more output: a JSON file plus a
small static frontend, published to a static host. No server, no database, and the ESPN cookies
never leave the Mac. Phase 6 later adds near-live data and chat bots using free services only
(GitHub Actions and a Cloudflare Worker), still with no always-on server.

```
EspnClient → LeagueValidator → WorkbookBuilder → .xlsx → Google Sheet   (unchanged)
                             ↘ LeagueStats → LeagueJson → SiteBuilder (league.json + web/) → SitePublisher → static host
```

Why this over a server app (Flask/FastAPI + hosting):

| | Static site (recommended) | Server app |
|---|---|---|
| Secrets | Stay on the Mac | ESPN cookies on a server |
| Cost / upkeep | Free (GitHub Pages / Cloudflare Pages), nothing to patch | Hosting, uptime, deploys |
| Freshness | Daily, same as the sheet | Could be live, but ESPN cookies still expire |
| Fits current design | Reuses the validated `LeagueData` and the "replace everything each run" model | New architecture |

## Decisions

1. **Who can see it: public, on GitHub Pages** (decided). Anyone with the URL can view it, so the
   site shows only league data (team names, stats, rosters), never cookies or IDs from `config.json`.
   Add `<meta name="robots" content="noindex">` so it stays out of search results.
2. **Where the built site lives:** a `gh-pages` branch of this repo, served at
   `https://renkecui.github.io/NBAFantasy26/`. Daily data commits stay off `main`.
   (Free GitHub Pages needs the repo to be public.)
3. **Keep the Google Sheet?** Recommended: yes, keep both until the site has proven itself.

## Phase 1: Compute the numbers in Python ✅ Done

Today Season Totals and every rank column are Excel formulas (`workbook/`), so the values only
exist once Google or Excel evaluates them. The site needs them as data.

- New `nbafantasy/stats/` with `LeagueStats(data: LeagueData)` (`league_stats.py`) that mirrors the formulas exactly:
  - weekly rank per category within each week (TO: lower is better), ties share the best rank
    (`COUNTIFS(...) + 1` semantics)
  - weekly average rank (col H) and overall weekly rank (col I)
  - season record and category W/L/T (counting `W`/`L`/`T`, ignoring `Live`)
  - season stats: FG%/FT% = average of weekly percentages, counting stats = sums
  - league rank per category (`RANK`, TO ascending)
- Unit tests with a small hand-built `LeagueData` fixture (ties, a bye week, a `Live` week).
- Optional later: have `WorkbookBuilder` cross-check its formulas against `LeagueStats`.

## Phase 2: Export the data ✅ Done

- New `nbafantasy/website/league_json.py` (`LeagueJson`, the JSON) and `site_builder.py` (`SiteBuilder`, writes `data/site/`):
  - `schema_version`, `generated_at`, `season_year`, `my_team`, team list with colors
  - `season_totals`, `weeks` (number, final, rows with stats + ranks), `rosters`
  - Built from an explicit allow-list of fields, so nothing from `config.json` can leak in.
- Write via temp file + rename, like the other outputs.

## Phase 3: Frontend (`web/`) ✅ Done

Plain HTML/CSS/JS, no build step (`index.html`, `style.css`, ES modules in `js/`) that fetches
`league.json` and renders:

| Page / tab | Contents | Interactions |
|---|---|---|
| Season Totals | Same columns as the sheet tab | Sort by any column; green→red color scale on ranks |
| Weekly Stats | One week at a time, `Live` badge on the current week | Week picker (defaults to latest), sort |
| Teams | One roster per team, your team first, team colors | Team picker, injury status badges |

- Hash routing (`#/season`, `#/weekly/7`, `#/team/<name>`) so links can be shared.
- Mobile: sticky first column and horizontal scroll inside the table (the sheet is ~27 columns wide).
- Light/dark theme, "Last updated" stamp from `generated_at`.
- Local preview: `python3 -m http.server -d data/site`.

## Phase 4: Publish from the daily run ✅ Built (turn on with `publish_site`, see [SETUP step 7](SETUP.md#7-optional-publish-the-website))

- New `nbafantasy/website/site_publisher.py` with `SitePublisher`: keep a `git worktree` of the `gh-pages`
  branch at `data/site-deploy/`, copy `web/` + `league.json` into it, commit only if something
  changed, and push. Each push uses the Mac's existing GitHub login, so no new secrets are needed.
- One-time setup: create the orphan `gh-pages` branch and turn on Pages
  (Settings → Pages → Deploy from branch → `gh-pages` / root).
- Keep history small: amend the single data commit (`push --force-with-lease`) instead of adding
  one commit per day.
- Wire into `SyncPipeline.run()` after validation, with flags `--site-only` and `--no-site`.
  (`--site-only` is also what the Phase 6 GitHub Actions workflow runs.)
- A failed site publish logs and notifies but doesn't block the Google Sheet update (and vice versa).
- Update `install.sh` (deploy credentials check), the pre-commit hook (block `data/site/` on `main`),
  README, SETUP and ARCHITECTURE.

## Phase 5: Later features (already in TODO)

- **Charts:** rank trends per team across weeks; the data is already in `league.json`, so this is
  frontend only (e.g. Chart.js from a CDN).
- **General Manager:** category strengths/weaknesses from `LeagueStats`, then AI-suggested trades.
  This needs an API key, which must never reach the browser. Before Phase 6, generate the tips in
  the daily Python run and ship them as JSON; with Phase 6 it becomes one of the chat bots.

## Phase 6: Live data and chat bots (free hosting)

GitHub Pages only serves files, and both features need code running with secrets (the ESPN cookies
and the Claude API key). This phase adds that code using **free services only, with no credit card
on file**. There is still no always-on server to run.

| Job | Service | Free plan |
|---|---|---|
| Host the site | **GitHub Pages** (unchanged) | Free for public repos |
| Fetch ESPN data on a schedule | **GitHub Actions** | Free minutes for public repos |
| Chat bots, league password, rate limits | **Cloudflare Worker** + Workers KV | Free plan, no card |

```
GitHub Actions (cron, every 15–30 min on game days)
   └─ python fantasy_update.py --site-only ──► ESPN → validate → stats → league.json ──► push gh-pages

browser ── GET league.json ─────────────────► GitHub Pages
        └─ POST /chat (league password) ────► Cloudflare Worker ──► Claude API
                                                 │ reads league.json from GitHub Pages
                                                 └ rate-limit counters in Workers KV
```

### Live data: GitHub Actions

- New workflow `.github/workflows/update-site.yml` on a `schedule:` cron (every 15–30 minutes
  during game hours) plus `workflow_dispatch` for a manual run.
- It runs the same Python pipeline as the Mac (`EspnClient` → `LeagueValidator` → `LeagueStats` →
  `LeagueJson`/`SiteBuilder`) with `--site-only`, then pushes to `gh-pages`. It takes over Phase 4's site
  publishing from the Mac; the Mac job keeps updating the Google Sheet.
- `league_id`, `season_year`, `my_team_name`, `espn_s2` and `SWID` become repository secrets.
  `Config` reads them from environment variables when `config.json` is missing.
- Skip the push when the data hasn't changed, and use a `concurrency:` group so two runs never
  overlap (the Actions version of `RunLock`).
- The page checks `league.json` (or a tiny `version.json`) every minute or two and re-renders only
  when `generated_at` changes.

Limits to accept:
- Scheduled runs can start several minutes late; the shortest interval is 5 minutes. Data is
  "near live" (about 15–30 minutes behind ESPN), not live during games.
- GitHub turns off scheduled workflows in a public repo after about 60 days without activity, so
  it may need re-enabling after the off-season.
- ESPN cookies expire. A failed run emails you; then paste new cookies into the repo secrets.

### Chat bots: Cloudflare Worker

- New folder `worker/` with a small JavaScript Worker (about 100 lines), deployed with `wrangler`.
- `POST /chat`: checks the league password, loads `league.json` from GitHub Pages (cached), builds
  a prompt from a compact summary (season totals, recent weekly ranks, rosters) plus the user's
  question, calls Claude and streams the answer back.
- Starting bots: a league Q&A bot ("who leads in steals?") and the General Manager trade adviser
  from Phase 5.
- Secrets (`ANTHROPIC_API_KEY`, `LEAGUE_PASSWORD`) are stored with `wrangler secret put`, never in
  the repo or in `web/`.
- The Worker allows requests only from the GitHub Pages origin (CORS).

### League password

See [TODO](TODO.md#league-password). Stats pages stay public; only the chat is protected.

- The page asks for the password once; the Worker checks it and returns a signed token
  (HMAC, expires after e.g. 30 days) that the page stores and sends with each chat request.
- Change the password by updating the Worker secret; that also logs everyone out.

### Cost and abuse controls

Hosting is free, but **Claude API calls are paid per use**, so these are required:

- Hard monthly spending limit in the Anthropic Console.
- Per-visitor rate limit (e.g. 20 messages/day) and a league-wide daily cap, counted in Workers KV.
- Default to the cheapest suitable model; cap message length and how much history is sent.
- Send a compact data summary instead of the whole `league.json`.

### Groundwork to do now so Phase 6 is easy

- Keep `stats/` and `website/` free of Mac-only code (no `osascript`, no launchd paths), so
  they run on GitHub's Linux runners.
- Let `Config` fall back to environment variables, and let notifications fall back to logging when
  `osascript` isn't available.
- Load the data URL from one constant (`League.DATA_URL` in `web/js/state/league.js`).
- Version the JSON (`schema_version`) so the frontend, the Worker and the exporter can change
  independently.

### If this outgrows the free setup

For true real-time updates during games, move everything to one Python app on **Google Cloud Run**
with Cloud Scheduler. One league likely stays inside its free tier, but it needs a credit card on
file. Other options considered and set aside: Render's free plan (sleeps when idle, slow first
reply), Vercel's free plan (scheduled jobs about once a day), Oracle Cloud Always Free (a server
to manage yourself), Fly.io and Railway (no real free tier).

## Possible follow-up: move the Google Sheet update off the Mac

Phase 6 moves the site's data fetch to GitHub Actions. The Google Sheet update could follow, but
the Google OAuth token would have to move into secrets too. Worth doing only once the site
replaces the sheet.

## Rough size

| Phase | Effort |
|---|---|
| 1. Stats in Python + tests | ~1 day |
| 2. JSON export | ~half a day |
| 3. Frontend | 1–2 days |
| 4. Publishing + docs | ~half a day |
| 6. Live data + chat | 2–4 days (Actions workflow, env-var config, chat Worker, password, rate limits) |
