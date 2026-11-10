# TODO

Open ideas. Done so far: the website, team color themes, and login (team name + league password).

## Live data

Refresh the website's data during the day instead of once a night, on free services only.

- A GitHub Actions workflow on a cron (every 15–30 minutes on game days, plus a manual run) runs
  `python fantasy_update.py --site-only` and pushes `web/league.json` when it changed. The Mac keeps
  updating the Google Sheet.
- ESPN settings and cookies become repository secrets; `Config` reads environment variables when
  `config.json` is missing, and notifications fall back to logging off the Mac.
- Use a `concurrency:` group so runs never overlap. The page re-renders when `generated_at` changes.
- Limits: scheduled runs can start late (data is ~15–30 minutes behind ESPN); GitHub pauses
  schedules after ~60 days without activity; expired ESPN cookies need pasting into the secrets.

## Chat bots

Let logged-in members ask about the league. The Cloudflare Worker gets a `POST /chat` that reuses
the login session, builds a prompt from a compact league summary and calls Claude.

- Bots: a league Q&A bot ("who leads in steals?") and the General Manager below.
- `ANTHROPIC_API_KEY` is a Worker secret, never in the repo.
- Claude calls cost money: set a monthly limit in the Anthropic Console, rate-limit per member and
  per day in Workers KV, use the cheapest suitable model, and cap message and history length.

## General Manager

AI tips on what your team is lacking, plus fair trade ideas with teams that have what you need.
Example: offer assists for another stat without checking every other team by hand.

## Charts

Charts of each team's rank trends through the season, colored with each team's theme (`TeamThemes`).
