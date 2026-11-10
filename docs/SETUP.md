# Setup

How to get Fantasy Report running. The scheduled updates run on GitHub Actions; a computer is only
needed once, to sign in to Google and copy a few values into GitHub. It takes about 20 minutes.

Back to the [README](../README.md) · See also [Architecture](ARCHITECTURE.md)

## What you need

- A computer with **Python 3** (`python3 --version` should work in a terminal), used once
- A **GitHub account** with this repository (public, for free GitHub Pages and Actions)
- A **Google account** (the sheet is created in its Drive)
- Access to the **ESPN fantasy basketball league** in Chrome

## 1. Get the code

```bash
git clone https://github.com/renkecui/FantasyReport.git
cd FantasyReport
```

The other commands in this guide are run from this folder.

## 2. Google: let the app create and update the sheet

1. Go to https://console.cloud.google.com and sign in.
2. Create a new project, for example `FantasyReport`.
3. Under **APIs & Services → Library**, enable both:
   - **Google Drive API**: uploads and updates the sheet (required)
   - **Google Sheets API**: adds the "this sheet is auto-updated" warning to each tab (optional; without it the log shows a harmless 403)
4. Under **APIs & Services → OAuth consent screen** (may be called **Google Auth Platform**):
   - User type **External**, app name `Fantasy Report`, your email for the contact fields.
   - Under **Audience**, add your Gmail as a **test user**.
   - Click **Publish app** so the status says **In production**. While it says "Testing",
     Google makes you sign in again every 7 days. No Google review is needed; the app only
     asks for access to files it creates.
5. Under **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type **Desktop app**.
   - **Download JSON**, rename it to `credentials.json`, and put it in the project folder.

## 3. ESPN: add your league details and login cookies

A private league needs two cookies from your ESPN login.

1. In Chrome, open https://fantasy.espn.com while logged in.
2. Press **Cmd + Option + I** → **Application** tab → **Cookies** → `https://fantasy.espn.com`.
3. Copy the **Value** of `espn_s2` (a long string) and `SWID` (looks like `{ABCD-1234-...}`, keep the braces).
4. Create your config file:
   ```bash
   cp config.example.json config.json
   ```
5. Fill in `config.json`:

   | Key | What to put |
   |---|---|
   | `league_id` | The number after `leagueId=` in your league's URL |
   | `season_year` | The season ESPN uses, e.g. `2027` for the 2026-27 season |
   | `my_team_name` | Your team's name exactly as ESPN shows it (its tab goes first in the Google Sheet; the website highlights whoever is logged in) |
   | `sheet_title` | Name for the Google Sheet (also the website's title) |
   | `espn_s2`, `swid` | The two cookie values |
   | `publish_site` | `true` to publish the website on manual runs too; leave `false` until step 5 |

> [!WARNING]
> Keep `config.json` private. Anyone with these cookies can use your ESPN account.
> It is git-ignored and never committed.

## 4. Local setup and Google login

```bash
scripts/setup.sh
```

This:
1. Creates a private `.venv/` and installs the Python packages into it (nothing system-wide).
2. Turns on the pre-commit hook that blocks secrets from being committed.
3. Opens your browser to sign in to Google. Pick your account and click **Allow**.
   If you see "Google hasn't verified this app", click **Advanced → Go to Fantasy Report**.
4. Runs once and prints the link to your new Google Sheet. The Google login is saved in
   `data/token.json` and the sheet's ID in `data/sheet_id.txt`; the next step copies both to GitHub.

## 5. Schedule the updates on GitHub Actions

The **Update league data** workflow (`.github/workflows/update.yml`) runs the update on GitHub's
servers at 8:00 AM and 5:00 PM New York time: it fetches ESPN, updates the Google Sheet, commits
`web/league.json` to `main` and deploys the website. It reads its settings from repository secrets
instead of `config.json`.

1. **Website:** open the repository's **Settings → Pages**. Under **Build and deployment → Source**,
   choose **GitHub Actions**.
2. **Secrets:** open **Settings → Secrets and variables → Actions** and add these
   **repository secrets** (the values are in `config.json` and `data/`):

   | Secret | Value |
   |---|---|
   | `LEAGUE_ID` | `league_id` |
   | `SEASON_YEAR` | `season_year` |
   | `ESPN_S2` | `espn_s2` |
   | `ESPN_SWID` | `swid` (with the braces) |
   | `GOOGLE_TOKEN_JSON` | the whole contents of `data/token.json` (`pbcopy < data/token.json` copies it on a Mac) |
   | `GOOGLE_SHEET_ID` | the contents of `data/sheet_id.txt` |
   | `MY_TEAM_NAME`, `SHEET_TITLE` | optional, same as in `config.json` |

   Without `GOOGLE_TOKEN_JSON` the workflow updates only the website. Until `LEAGUE_ID` is set,
   scheduled runs skip quietly.
3. **Check it:** open the **Actions** tab, pick **Update league data**, and click **Run workflow**.
   It should finish green, and the log should end with `Updated Google Sheet: https://docs.google.com/...`.
   After a minute or two the site is at `https://<your-github-name>.github.io/FantasyReport/`.

> [!NOTE]
> The website is public to anyone with the link. It shows team names, stats and rosters exactly as
> ESPN has them (check that no team name is something private, such as an email address).
> It never includes `config.json`, cookies or IDs, and asks search engines not to list it.

Good to know:
- A failed run emails you (GitHub's default for scheduled workflows). Warnings, such as "the sheet was
  edited and backed up", show on the run's summary page.
- Runs can start a few minutes late. GitHub pauses scheduled workflows after 60 days without
  any commits (e.g. the off-season); turn it back on in the Actions tab.
- Edits people made to the sheet are backed up before each update; download them from the run's
  **Artifacts** (kept 90 days).
- Everything lives on `main`: the site's code in `web/` and the data in `web/league.json`, which each
  run commits as "Update league data (date)" when the numbers change. Run `git pull` before new work.
  Any push that changes `web/` redeploys the site.

## 6. (Optional) Turn on login and team themes (Cloudflare Worker)

Every team already has its own color on the website. To let people **log in** (their team +
the league password) and **pick their team's color theme**, run the small API in `worker/` on
Cloudflare's free plan. Without it, login is hidden and every team keeps its default theme.

1. Create a free account at https://dash.cloudflare.com/sign-up (no credit card needed).
2. In Terminal, from the project folder:
   ```bash
   cd worker
   npm install
   npx wrangler login
   npx wrangler kv namespace create KV
   ```
   `wrangler login` opens your browser to allow access. The last command prints an `id`;
   paste it into `worker/wrangler.toml` in place of `REPLACE_WITH_KV_NAMESPACE_ID`.
3. Set the two secrets. Each command asks you to type the value (it is never saved in the repo):
   ```bash
   npx wrangler secret put LEAGUE_PASSWORD
   npx wrangler secret put TOKEN_SECRET
   ```
   `LEAGUE_PASSWORD` is what you give the league. For `TOKEN_SECRET`, use a long random value,
   e.g. the output of `openssl rand -hex 32`.
4. Put it online:
   ```bash
   npx wrangler deploy
   ```
   It prints the Worker's address, like `https://nbafantasy-api.<your-name>.workers.dev`.
   The first time, Cloudflare asks you to register a `workers.dev` subdomain for your account
   (Workers & Pages in the dashboard); deploy again afterwards.
5. Put that address in `web/index.html`:
   `<meta name="nbafantasy-api" content="https://nbafantasy-api.<your-name>.workers.dev">`,
   then commit and push to `main`. The site redeploys, and from then on visitors see a
   login screen (username = their team name, password = the league password) before any league data.

Good to know:
- **Changing the password**: run `npx wrangler secret put LEAGUE_PASSWORD` again. Everyone is logged out.
- **"Remember me"** keeps people logged in until `SESSION_END` in `worker/wrangler.toml` (the end of
  the season); without it, a login lasts 12 hours or until the browser closes.
- Five wrong passwords from one connection lock login for 15 minutes.
- The site's address is in `ALLOWED_ORIGINS` in `worker/wrangler.toml`; only that site can use the API.
- Test locally: copy `worker/.dev.vars.example` to `worker/.dev.vars`, run `npm run dev` in `worker/`,
  and set the meta tag in `data/site/index.html` (not `web/`) to `http://127.0.0.1:8787` while previewing.
- Worker tests: `cd worker && npm test`.

---

## Everyday use

The scheduled runs need nothing from you. For a run by hand (needs step 4 on that computer):

| Task | Where / command |
|---|---|
| Update now | Actions tab → **Update league data** → **Run workflow** |
| See what happened | Actions tab → the run's log |
| Find the sheet link | The end of the run's log, or the `GOOGLE_SHEET_ID` secret |
| Stop the scheduled updates | Actions tab → **Update league data** → **⋯ → Disable workflow** |
| Update from this computer | `python3 fantasy_update.py` |
| Local files only (`.xlsx` and `data/site/`), publish nothing | `python3 fantasy_update.py --excel` |
| Preview the website | `python3 -m http.server -d data/site`, then open http://localhost:8000 |

Each update replaces the whole sheet. Don't keep notes in it. If someone does edit it, a copy
is saved before it is replaced (in the run's Artifacts, or `data/backups/` for a local run).

## Troubleshooting

Every failure is in the run's log, and a failed scheduled run emails you.

| The log says | Fix |
|---|---|
| `config.json not found and LEAGUE_ID ... not set` | Add the secrets (step 5). |
| `GOOGLE_SHEET_ID secret is missing` | Add it from `data/sheet_id.txt` (step 5). |
| `Google login missing or expired` | Run `python3 fantasy_update.py --login` on your computer, then copy the new `data/token.json` into `GOOGLE_TOKEN_JSON`. |
| `ESPN refused the request` / `ESPNAccessDenied` | The ESPN cookies expired. Get fresh ones (step 3) and update `ESPN_S2` / `ESPN_SWID`. |
| `No matchups found` | Check `LEAGUE_ID` and `SEASON_YEAR`. |
| `team '…' not found` | Fix `MY_TEAM_NAME`; the log lists ESPN's team names. |
| `ESPN data looks wrong` | Usually ESPN is mid-update. The next run normally works. |
| `can no longer edit the Google Sheet` | Sharing changed. Make sure your account still owns or can edit it. |
| `could not add the edit warning` (HTTP 403) | Enable the Google Sheets API (step 2). The data still updated. |
| `A NEW Google Sheet link was created` | The old sheet was deleted or trashed. Put the new ID from the log into `GOOGLE_SHEET_ID` and share the new link with the league. |
| `Website publish failed` | Re-run the workflow; check that **Settings → Actions → General → Workflow permissions** allows write access. |
| Site shows the README or an old version | Settings → Pages → Source must be **GitHub Actions**; check the **Deploy website** run in the Actions tab. |

## Moving from the Mac schedule

Older versions ran the update on a Mac with a launchd job (`scripts/install.sh`). Once the GitHub
workflow runs green (step 5), remove the Mac's job so both don't update:

```bash
scripts/remove-mac-schedule.sh
```

The Full Disk Access entry for Python that the old setup needed can also be removed in
**System Settings → Privacy & Security → Full Disk Access**.
