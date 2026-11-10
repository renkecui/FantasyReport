# TODO

Below lists additional ideas to implement for this project

## Core

### Webpage

Create a webpage for the poject

- Each table should be displayed on the webpage
- Plan: [WEBSITE_PLAN.md](WEBSITE_PLAN.md) (static site on GitHub Pages, built by the daily run)
- Status: done (Phases 1–4). Turn on publishing with `publish_site` in `config.json`

### Live Data and Chat Bots

Refresh the website's data during the day and let users ask chat bots about the league, using free services only

- ESPN data fetched by GitHub Actions every 15–30 minutes on game days
- Chat bots run on a Cloudflare Worker that calls Claude (the API is the only paid part)
- See Phase 6 in [WEBSITE_PLAN.md](WEBSITE_PLAN.md)

## Features to Add

### General Manager

AI generated tips on what your team is lacking, and then looks at other teams to generate ideas for fair trades

Example: Give away assists for another stat so I don't need to look at every other team to see who needs assists and can offer me something good

### Charts

Display charts show team ranking trends throughout the season

### Color Styling

Add color to the website's tables and charts

Status: done. Themes are in `web/themes.json`; picking needs the Cloudflare Worker deployed ([SETUP step 8](SETUP.md#8-optional-turn-on-login-and-team-themes-cloudflare-worker)). Charts don't exist yet; they should color teams with `TeamThemes`.

- Rankings use a green-to-red scale: best rank is green, worst is red
- Each team has its own color theme, used wherever that team appears (tables, charts, roster pages)
- Once [User Login](#user-login) exists, a logged-in user can change their team's theme by picking from a supplied list
- A theme can belong to only one team: themes already taken by other teams can't be selected
- Each team starts with a different default theme

### League Password

Protect the chat bots on the website with a shared league password, so only league members can use them (and spend AI credits)

Status: the password and login are built (Worker secret `LEAGUE_PASSWORD`); the chat bots that it will protect are still to do.

- Stats pages stay public; only the chat needs the password
- Checked by the Cloudflare Worker, stored as a Worker secret, never in the repo
- See Phase 6 in [WEBSITE_PLAN.md](WEBSITE_PLAN.md)

### User Login

Let users log in with their username (their team name) and the league password, and remember them so they don't need to re-enter it every visit

Status: done in `worker/` and `web/js/state/session.js`; goes live once the Worker is deployed ([SETUP step 8](SETUP.md#8-optional-turn-on-login-and-team-themes-cloudflare-worker)). `my_team_name` in `config.json` now only affects the Google Sheet.

- Username is picked from the league's team names; the password is the shared league password above
- Knowing who is logged in lets the site default to their team (e.g. highlight it in tables, personalize General Manager tips)
- "My team" must not be hard-coded to one user (Iren). Today it comes from `my_team_name` in `config.json` and is baked into `league.json` as `my_team`. On the website it should come from whoever is logged in, with no highlighted team when nobody is (`web/js/state/league.js` `myTeam` / `isMine`, `team-page.js` default team)
- Add a "Remember me" option that saves the login in the browser; add a "Log out" button that clears it
- Save a session token issued by the Cloudflare Worker after a successful login, not the raw password, and let it expire (e.g. after the season)
