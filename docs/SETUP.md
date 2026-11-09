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
   | `my_team_name` | Your team's name exactly as ESPN shows it (its tab goes first) |
   | `sheet_title` | Name for the Google Sheet |
   | `espn_s2`, `swid` | The two cookie values |

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

---

## Everyday use

| Task | Command |
|---|---|
| Update now | `python3 fantasy_update.py` |
| Save only the local `.xlsx`, skip Google | `python3 fantasy_update.py --excel` |
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

## Updating from an older version

Older versions kept `token.json`, `sheet_id.txt`, `sync_state.json`, the `.xlsx` and `backups/`
in the project folder, and had `install.sh` at the top level. After pulling:

1. Run any update (`python3 fantasy_update.py`). It moves those files into `data/`, keeping your sheet link.
2. Run `scripts/install.sh` once so the schedule uses `.venv/` and logs to `data/update.log`.
