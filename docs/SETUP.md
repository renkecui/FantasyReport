# Setup

How to get NBAFantasy26 running on your Mac. It takes about 15 minutes, once.

Back to the [README](../README.md) · See also [Architecture](ARCHITECTURE.md)

## What you need

- A Mac with **Python 3** (`python3 --version` should work in Terminal)
- A **Google account** (the sheet is created in its Drive)
- Access to the **ESPN fantasy basketball league** in Chrome

## 1. Get the code

```bash
git clone https://github.com/renkecui/NBAFantasy26.git
cd NBAFantasy26
```

The other commands in this guide are run from this folder.

## 2. Google: let the app create and update the sheet

1. Go to https://console.cloud.google.com and sign in.
2. Create a new project, for example `NBAFantasy26`.
3. Under **APIs & Services → Library**, enable both:
   - **Google Drive API**: uploads and updates the sheet (required)
   - **Google Sheets API**: adds the "this sheet is auto-updated" warning to each tab (optional; without it the log shows a harmless 403)
4. Under **APIs & Services → OAuth consent screen** (may be called **Google Auth Platform**):
   - User type **External**, app name `NBAFantasy26`, your email for the contact fields.
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
   | `publish_site` | `true` to publish the website every run (step 7); leave `false` until then |

> [!WARNING]
> Keep `config.json` private. Anyone with these cookies can use your ESPN account.
> It is git-ignored and never committed.

## 4. Install and schedule

```bash
scripts/install.sh
```

This:
1. Creates a private `.venv/` and installs the Python packages into it (nothing system-wide).
2. Opens your browser to sign in to Google. Pick your account and click **Allow**.
   If you see "Google hasn't verified this app", click **Advanced → Go to NBAFantasy26**.
3. Runs once and prints the link to your new Google Sheet.
4. Schedules a daily 8:00 AM run with launchd. If the Mac is asleep, it runs when it wakes.
5. Turns on the pre-commit hook that blocks secrets from being committed.

## 5. Let the scheduled run read the folder (Full Disk Access)

macOS blocks background programs from reading protected folders such as Downloads and
Documents, so the 8:00 AM run can fail even though running it by hand works.

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Click **+**, press **Cmd + Shift + G**, and paste the Python path that `scripts/install.sh`
   printed at the end. Click **Open** and make sure the switch is on.

## 6. Check that it works

Run the scheduled job right now:

```bash
launchctl kickstart gui/$(id -u)/com.renke.fantasyupdate
```

Then look at the end of the log:

```bash
tail -3 data/update.log | cut -c1-200
```

The last line should end with `Updated Google Sheet: https://docs.google.com/...`.

## 7. (Optional) Publish the website

Every run builds the website in `data/site/`. To put it online with GitHub Pages:

1. Make sure `git push` works from this folder (the run pushes with your normal GitHub login).
2. On GitHub, open the repository's **Settings → Pages**. Under **Build and deployment → Source**,
   choose **GitHub Actions**. Free GitHub accounts need the repository to be public for this.
3. Publish once by hand. This commits today's `web/league.json` to `main` and pushes it, and the
   **Deploy website** workflow (`.github/workflows/pages.yml`) puts `web/` online:
   ```bash
   python3 fantasy_update.py --site-only
   ```
4. Add `"publish_site": true` to `config.json` so the daily run updates it too.

After a minute or two the site is at `https://<your-github-name>.github.io/NBAFantasy26/`
(the log prints the link).

> [!NOTE]
> The website is public to anyone with the link. It shows team names, stats and rosters exactly as
> ESPN has them (check that no team name is something private, such as an email address).
> It never includes `config.json`, cookies or IDs, and asks search engines not to list it.

Everything lives on `main`: the site's code in `web/`, and the data in `web/league.json`, which the
run commits as "Update league data (date)" whenever the numbers change (a new timestamp alone isn't
committed). The run makes that commit in its own checkout of `main` in `data/site-deploy/`, so it never
touches the branch or files you're working on; deleting that folder is safe. Run `git pull` on `main`
before starting new work to pick up the data commits. Any push that changes `web/` (including merging
a working branch into `main`) redeploys the site.

## 8. (Optional) Turn on login and team themes (Cloudflare Worker)

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
5. Put that address in `web/index.html`:
   `<meta name="nbafantasy-api" content="https://nbafantasy-api.<your-name>.workers.dev">`,
   then commit and push to `main`. The site redeploys and shows **Log in** in the header.

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

| Task | Command |
|---|---|
| Update now | `python3 fantasy_update.py` |
| Local files only (`.xlsx` and `data/site/`), publish nothing | `python3 fantasy_update.py --excel` |
| Update only the website | `python3 fantasy_update.py --site-only` |
| Skip the website this run | `python3 fantasy_update.py --no-site` |
| Preview the website | `python3 -m http.server -d data/site`, then open http://localhost:8000 |
| Sign in to Google again | `python3 fantasy_update.py --login` |
| See what happened | `tail data/update.log` |
| Find the sheet link | Last line of `data/update.log`, or the ID in `data/sheet_id.txt` |
| Stop the daily run | `scripts/uninstall.sh` |
| Turn it back on | `scripts/install.sh` |

Each update replaces the whole sheet. Don't keep notes in it. If someone does edit it, a copy
is saved to `data/backups/` before it is replaced.

## Troubleshooting

Every failure shows a Mac notification and is written to `data/update.log`.

| The log says | Fix |
|---|---|
| `Google login missing or expired` | `python3 fantasy_update.py --login` |
| `ESPN refused the request` / `ESPNAccessDenied` | The ESPN cookies expired. Repeat step 3 with fresh cookies. |
| `Operation not permitted` | Redo step 5 (Full Disk Access). |
| `No matchups found` | Check `league_id` and `season_year` in `config.json`. |
| `team '…' not found` | Fix `my_team_name` in `config.json`; the log lists ESPN's team names. |
| `ESPN data looks wrong` | Usually ESPN is mid-update. The next run normally works. |
| `can no longer edit the Google Sheet` | Sharing changed. Make sure your account still owns or can edit it. |
| `Another update is already running` | Wait a few minutes. A lock left by a crash clears itself; if not, delete `data/.update.lock`. |
| `could not add the edit warning` (HTTP 403) | Enable the Google Sheets API (step 2). The data still updated. |
| `A NEW Google Sheet link was created` | The old sheet was deleted or trashed. Share the new link with the league. |
| `Website publish failed at 'git push'` | Check that `git push` works from this folder. The Google Sheet still updated. |
| `Website publish failed` (other) | Delete `data/site-deploy/` and run `python3 fantasy_update.py --site-only`. |
| Site shows the README or an old version | Settings → Pages → Source must be **GitHub Actions**; check the **Deploy website** run in the Actions tab. |

## Updating from an older version

Older versions kept `token.json`, `sheet_id.txt`, `sync_state.json`, the `.xlsx` and `backups/`
in the project folder, and had `install.sh` at the top level. After pulling:

1. Run any update (`python3 fantasy_update.py`). It moves those files into `data/`, keeping your sheet link.
2. Run `scripts/install.sh` once so the schedule uses `.venv/` and logs to `data/update.log`.
