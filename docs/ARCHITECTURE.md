# Architecture

How the project fits together. Back to the [README](../README.md) · See also [Setup](SETUP.md)

## Overview

**The scheduled update** (twice a day on GitHub Actions, or `python3 fantasy_update.py` by hand):

```mermaid
flowchart LR
    A["update.yml<br/>7 AM + 3 PM ET"] --> B["EspnClient<br/>fetch league"]
    B --> C{"LeagueValidator<br/>complete?"}
    C -- no --> X["Stop<br/>nothing changes"]
    C -- yes --> D["WorkbookBuilder<br/>.xlsx"]
    C -- yes --> E["LeagueJson<br/>league.json"]
    D --> F["GoogleSheetPublisher<br/>Google Sheet"]
    E --> G["SitePublisher + pages.yml<br/>GitHub Pages"]
```

**The website** (static files on GitHub Pages; login and themes on a Cloudflare Worker):

```mermaid
flowchart LR
    U["Browser<br/>web/js"] -- "page + league.json" --> P["GitHub Pages"]
    U -- "login, themes" --> W["Cloudflare Worker<br/>worker/"]
    W -- "team names" --> P
    W --> K[("Workers KV<br/>theme picks, rate limits")]
```

## How a run works

1. **Start.** The **Update league data** workflow (`.github/workflows/update.yml`) runs
   `fantasy_update.py` on GitHub's servers at 7:00 AM and 3:00 PM New York time. Cron is in UTC, so
   each time is scheduled at both daylight-saving hours and only the one that is 8 / 5 in New York
   continues. It writes the `GOOGLE_TOKEN_JSON` / `GOOGLE_SHEET_ID` secrets to `data/`, and `Config`
   reads the other secrets as environment variables because there is no `config.json`. You can also
   run it by hand on a computer; then, if `.venv/` exists, the script restarts itself with that Python.
2. **Prepare.** `Paths.prepare()` creates `data/` and moves files that older versions left in
   the project folder.
3. **Lock.** `RunLock` creates `data/.update.lock` holding the process ID, so two runs on one
   computer can't overlap (on GitHub, the workflow's `concurrency` group does the same).
4. **Fetch.** `EspnClient` loads the league once, which includes every team's roster. It then
   reads the scoreboard and box scores for each matchup period up to the current one.
5. **Validate.** `LeagueValidator` refuses data that looks incomplete. If it fails, nothing is
   written and the Google Sheet is left alone.
6. **Build.** `WorkbookBuilder` writes the styled workbook to a temp file and renames it to
   `data/Fantasy_Report.xlsx`.
7. **Publish** (skipped with `--excel`). `GoogleSheetPublisher` checks the live sheet:
   - edited since the last sync, or last changed by someone else → download a backup to `data/backups/`
     first (if that fails, stop); on GitHub the workflow keeps it as a run artifact for 90 days
   - deleted, trashed or no longer a Sheet → create a new one and warn you to re-share it
   - no edit access → stop

   Then it uploads the `.xlsx`, which Drive converts to the Google Sheet, adds the edit warning
   to each tab, and records the sheet's `modifiedTime` in `data/sync_state.json`.
8. **Build the website.** `LeagueJson` uses `LeagueStats` to compute the same ranks and totals
   the sheet's formulas show; `SiteBuilder` copies `web/` and writes `league.json` into `data/site/`.
9. **Publish the website** (when `publish_site` is `true` or with `--site-only`; never with
   `--excel` or `--no-site`). `SitePublisher` keeps a detached checkout of `main` in
   `data/site-deploy/` (so it never touches a working branch), copies the new `league.json` to
   `web/league.json`, commits only that file and pushes to `main`. Nothing is committed when only the
   timestamp changed; if someone else pushed meanwhile, it rebuilds on top and tries once more. The
   **Deploy website** workflow (`.github/workflows/pages.yml`) then deploys `web/` to GitHub Pages
   (`update.yml` calls it directly, because a push made by a workflow doesn't start other workflows). Google and the website
   are published independently: if one fails, the other still runs, and the run reports the failure.
10. **Report.** Success or failure goes to the log (stdout). On GitHub, warnings and errors also show
    on the run's summary page, and a failed run (exit 1) emails you.

## Code layout

One class per file, and each file is named after its class (`LeagueStats` → `league_stats.py`,
`SortableTable` → `sortable-table.js`).

```
fantasy_update.py                 entry point: .venv switch, then Application(root).main()
nbafantasy/
├── app/
│   ├── application.py            Application (singleton): paths, run lock, logging failures
│   ├── sync_pipeline.py          SyncPipeline: the steps of a run (fetch, build, publish)
│   └── run_options.py            RunOptions: the command-line flags
├── common/
│   ├── singleton.py              Singleton: metaclass, one instance per process
│   ├── sync_error.py             SyncError: a known problem that stops the run
│   ├── logger.py                 Logger (singleton): the run's log; GitHub annotations on Actions
│   ├── files.py                  Files: atomic write, read
│   ├── retry_policy.py           RetryPolicy: retries temporary errors
│   └── run_lock.py               RunLock: stops two runs overlapping
├── config/
│   ├── paths.py                  Paths: where every file lives
│   └── config.py                 Config: config.json, or environment variables (GitHub secrets)
├── models/
│   ├── categories.py             Categories: the 9 scoring categories and player stats
│   ├── league_data.py            LeagueData
│   ├── week.py                   Week
│   ├── matchup_row.py            MatchupRow
│   ├── team_roster.py            TeamRoster
│   └── player.py                 Player
├── espn/
│   ├── espn_client.py            EspnClient: ESPN -> LeagueData
│   └── league_validator.py       LeagueValidator: data checks before anything is replaced
├── stats/
│   ├── ranking.py                Ranking: tie-aware ranks ("1, 2, 2, 4")
│   ├── league_stats.py           LeagueStats: weekly ranks and season totals
│   ├── weekly_row.py             WeeklyRow
│   └── season_row.py             SeasonRow
├── workbook/
│   ├── workbook_builder.py       WorkbookBuilder: the whole .xlsx
│   ├── theme.py                  Theme: fonts, colors, borders
│   ├── sheet_writer.py           SheetWriter: base class for a tab
│   ├── season_totals_sheet.py    SeasonTotalsSheet
│   ├── weekly_stats_sheet.py     WeeklyStatsSheet
│   └── team_roster_sheet.py      TeamRosterSheet
├── google_sheets/
│   ├── google_sheet_publisher.py GoogleSheetPublisher: .xlsx -> the shared Google Sheet
│   ├── google_auth.py            GoogleAuth: the saved Google login
│   ├── sync_state.py             SyncState: when the sheet was last written
│   ├── sheet_check.py            SheetCheck: what the live sheet looks like before an update
│   └── sheet_publish_result.py   SheetPublishResult
└── website/
    ├── league_json.py            LeagueJson: what goes into league.json
    ├── site_builder.py           SiteBuilder: web/ + league.json -> data/site/
    ├── site_publisher.py         SitePublisher: league.json -> web/league.json on main
    └── site_publish_result.py    SitePublishResult
web/
├── index.html, style.css         the page and its styles
├── themes.json                   the team color themes
└── js/                           ES modules, one class each (see "Website" below); main.js starts the app
worker/                           Cloudflare Worker: login and team themes (src/, test/, wrangler.toml)
tests/                            one test file per class (test_league_stats.py, ...); sample_league.py
                                  holds SampleLeague, a made-up league for tests
scripts/                          setup.sh (venv + Google login), remove-mac-schedule.sh (old launchd job)
.github/workflows/update.yml      the scheduled update: 7 AM / 3 PM New York time, then deploys the site
.github/workflows/pages.yml       deploys web/ to GitHub Pages when it changes on main
.github/workflows/worker.yml      tests and deploys worker/ to Cloudflare when it changes on main
requirements.txt                  Python packages (used by setup.sh and the workflow)
.githooks/pre-commit              blocks commits of private files and secrets
```

Each step is a class that receives what it needs (`Config`, `Paths`, `RetryPolicy`) in its
constructor, and steps exchange only the plain data objects in `models/`. There are no
module-level functions: helpers are static methods on a class (`Files`, `Ranking`).

**Singletons.** Classes that must exist once per process use the `Singleton` metaclass:
`Logger` (the one log stream) and `Application`. Calling the class returns the same
instance every time; `reset()` exists for tests. Data and settings (`Paths`, `Config`) are
deliberately *not* singletons, so tests can build them with different values.

**Website (`web/js/`)** follows the same layout with ES modules, one class per file:

| File | Class | Role |
|---|---|---|
| `util/dom.js`, `util/format.js`, `util/rank-color.js` | `Dom`, `Format`, `RankColor` | Stateless helpers (static methods): building elements, number formats, rank colors |
| `shared/theme-assignment.js` | `ThemeAssignment` | Which theme each team has; also used by the Worker, so both agree |
| `state/preferences.js` | `Preferences` (singleton) | The viewer's switch choices, kept in `localStorage` |
| `state/league.js` | `League` (singleton) | Loads `league.json` and answers lookups (standings, a team's history) |
| `state/api-client.js` | `ApiClient` (singleton) | Calls the Worker; its address is the `nbafantasy-api` meta tag in `index.html` |
| `state/session.js` | `Session` (singleton) | Who is logged in: the Worker's signed token (never the password), in `localStorage` with "Remember me", else `sessionStorage` |
| `state/team-themes.js` | `TeamThemes` (singleton) | Each team's color theme, from the Worker or, without one, the defaults |
| `components/widgets.js` | `Widgets` | Shared pieces: team name with color dot, result badges, the switches |
| `components/sortable-table.js` | `SortableTable` | A table whose columns sort on click; remembers each table's sort |
| `components/account-menu.js` | `AccountMenu` | The header's menu for the logged-in team: "Team theme…" and "Log out" |
| `components/login-gate.js` | `LoginGate` | The login screen shown until someone logs in (username = team name, any case; league password) |
| `components/theme-dialog.js` | `ThemeDialog` | Pick a free theme |
| `pages/page.js` → `season-page.js`, `weekly-page.js`, `team-page.js` | `Page` → `SeasonPage`, `WeeklyPage`, `TeamPage` | One class per page; the base class builds the category columns |
| `router.js` | `Router` | Maps `#/season`, `#/weekly/<n>`, `#/team/<name>` to a page |
| `app.js` | `App` (singleton) | Loads the data, then shows the login screen or the current page |
| `main.js` | (none) | Entry point: `App.instance().start()` |

The JavaScript singletons are created with `X.instance()`; calling `new X()` a second time throws.

**Team colors.** `web/themes.json` lists the themes (id, name, color). Every team has one, and no
two teams share one: a team keeps the theme it picked, the others get a default by league order.
Pages set `--team` on anything that belongs to a team (rows, matchup cards, the team page, picker
chips, dots) and the CSS colors it from there. The logged-in team's rows are tinted with its color.

**Login and themes (`worker/`).** A Cloudflare Worker, one class per file in `worker/src/`:

| File | Class | Role |
|---|---|---|
| `index.js` | (none) | Worker entry point: every request goes to `ApiWorker` |
| `api-worker.js` | `ApiWorker` | Routes `GET /themes`, `POST /login`, `GET /me`, `PUT /me/theme`; CORS for the site |
| `login-service.js` | `LoginService` | Checks team + league password (compared via SHA-256 digests), issues a session token |
| `session-token.js` | `SessionToken` | Signs and verifies tokens (HMAC-SHA256). The key includes the password, so changing it logs everyone out |
| `rate-limiter.js` | `RateLimiter` | Five tries per connection per 15 minutes, counted in Workers KV |
| `theme-registry.js` | `ThemeRegistry` | Theme picks in Workers KV; refuses a theme another team has (409) |
| `league-teams.js` | `LeagueTeams` | The valid team names, read from the published `league.json` |
| `http.js`, `http-error.js` | `Http`, `HttpError` | JSON responses, CORS headers, request bodies, errors |

The league password and token key are Worker secrets, never in the repo. `worker/test/` runs with
`node --test` against an in-memory KV.

## Data model

| Class | Holds |
|---|---|
| `LeagueData` | `teams` (ESPN order), `weeks`, `rosters` (team name → `TeamRoster`), `my_team` |
| `Week` | `number`, `final` (finished or in progress), `rows` |
| `MatchupRow` | One team's side of a matchup: opponent, category W/L/T, result (`W`/`L`/`T`/`Live`), the 9 category stats |
| `TeamRoster` | A team's `players`, sortable into lineup order |
| `Player` | Lineup slot, name, NBA team, positions, injury status, season per-game averages |

The league uses 9-category head-to-head scoring: FG%, FT%, 3PM, REB, AST, STL, BLK, TO, PTS.
For TO, fewer is better.

## Sheet tabs

| Tab | Class | Contents |
|---|---|---|
| Season Totals | `SeasonTotalsSheet` | Record, category W/L/T, season stats and league rank per category. All formulas over Weekly Stats. |
| Weekly Stats | `WeeklyStatsSheet` | Every team's matchup each week, its 9 stats, and its rank that week. The week in progress shows `Live`. |
| *Team name* (one per team) | `TeamRosterSheet` | Current roster with season averages. Your team first with a green tab; other tabs use the team's color. |

Season FG% and FT% are the average of the weekly percentages. On roster tabs, FG% and FT% are
formulas (made ÷ attempted). Tab names are cleaned to meet Google's rules: no `[]:*?/\`,
at most 31 characters, and unique.

## Website

`league.json` (schema version 2) holds:

- `teams`: names in ESPN order (no "my team": the site uses whoever is logged in)
- `season`: record, category record, stats, league ranks, average rank, weeks played, and
  `per_week` averages with their own ranks; `season_completed` is the same from finished weeks only
- `weeks`: each team's matchup row with stats, weekly ranks, average and overall rank
- `rosters`: players in lineup order with per-game averages (FG%/FT% as made ÷ attempted)

It is built from an allow-list of fields, so nothing from `config.json` can reach it.

`web/js/` renders three hash-routed pages (`#/season`, `#/weekly/<n>`, `#/team/<name>`) with no
libraries or build step. Every table sorts by any column, category cells are tinted by rank
(green = 1st, red = last), and a Stats/Ranks switch shows values or ranks. The Season page also
switches between totals and per-week averages (fair to teams that had a bye) and, while a week is
in progress, between including and excluding it. Switches are remembered in `localStorage`.

`LeagueStats` mirrors the workbook formulas (and also builds `season_completed`, which leaves the
week in progress out of everything): weekly rank = 1 + teams strictly better that week
(TO: fewer is better), overall = rank of the average category rank, season W/L/T counts finished
weeks only, category record and counting stats sum every week, FG%/FT% average the weekly
percentages, and league rank uses the same tie rule ("1, 2, 2, 4").

## Safety checks

| Situation | What happens |
|---|---|
| ESPN data incomplete | Validation fails and nothing changes. Checks: at least 2 teams; 2 rows per matchup in each finished week (one bye allowed when the team count is odd); category scores add up to 9; every team has a roster; `my_team_name` exists. |
| Someone edited the sheet | Detected by comparing `modifiedTime` with `data/sync_state.json`. A backup goes to `data/backups/` (last 20 kept) before replacing. If the backup fails, the run stops. |
| Sheet deleted or trashed | A new sheet is created and a warning says to re-share it (on GitHub, also put the new ID into `GOOGLE_SHEET_ID`). |
| Lost edit access | The run stops; nothing changes. |
| Temporary errors | Up to 3 tries with growing waits for network errors, Google 429/5xx and rate-limit 403s. ESPN login errors and other 4xx errors fail immediately. |
| Website publish fails | Logged; the Google Sheet update still happens (and the other way round). The run exits with an error. |
| Website unchanged | No commit and no push. |
| Crash mid-write | The token, sheet ID, state and `.xlsx` are written to a temp file and then renamed, so they're never left half-written. |

## External services

| Service | Used for | Access |
|---|---|---|
| ESPN Fantasy API (`espn-api` package) | League, matchups, box scores, rosters | `espn_s2` + `SWID` cookies |
| Google Drive API v3 | Upload/convert the sheet, check it, export backups | OAuth, `drive.file` scope (only files this app created) |
| Google Sheets API v4 | Edit-warning protection on each tab (optional) | Same OAuth login |
| GitHub Actions | **Update league data**: the scheduled run at 7 AM / 3 PM New York time; **Deploy website**: publishes `web/` | Repository secrets (ESPN, Google), read as environment variables; the built-in token pushes `web/league.json` and deploys Pages |
| GitHub Pages | Hosts the website | Public |

## Design decisions

- **Replace the whole sheet each run** instead of editing cells. Every run produces a complete,
  consistent sheet, and the formulas and styling come from one place (`workbook/`). The cost is
  that manual edits are overwritten, which is why edits are backed up and tabs carry a warning.
- **Formulas instead of computed numbers** in Season Totals and the rank columns, so the sheet
  shows how each number is derived and recalculates if a value is corrected.
- **The website is static and built by the same run**, so it reuses the validated data, needs no
  server, and the ESPN cookies stay in GitHub's encrypted secrets. Later ideas are in [TODO.md](TODO.md).
- **Everything on `main`.** The site's code and its data (`web/league.json`) live on one branch;
  a data commit is added only when the numbers change. New work happens on working branches merged
  into `main`. GitHub Actions deploys `web/`, so no separate site branch is needed.
- **`drive.file` scope only**: the app can't see anything else in your Drive.
- **Files you provide vs. files the app writes**: `config.json` and `credentials.json` sit in the
  project folder; everything generated lives in `data/`. Both are git-ignored.
