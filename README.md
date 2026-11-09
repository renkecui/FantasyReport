# NBAFantasy26: ESPN → Google Sheets, every day at 8:00 AM

Every morning at 8:00 AM this pulls your ESPN league  and
updates one Google Sheet with three tabs: Season Totals, Weekly Stats and IRen Roster.
The sheet keeps the same link every day. A local Excel copy is also saved in this folder.

If your Mac is asleep at 8:00, the update runs as soon as it wakes up.

---

## One-time setup (about 15 minutes)

### Step 1. Google: let the script edit your sheet

1. Go to https://console.cloud.google.com and sign in with your Google account.
2. Create a new project. Name it something like `NBAFantasy26`.
3. Go to **APIs & Services → Library**, search **Google Drive API**, and click **Enable**.
4. Go to **APIs & Services → OAuth consent screen** (may be called **Google Auth Platform**).
   - User type: **External**. App name: `NBAFantasy26`. Use your email for the contact fields.
   - Under **Audience**, add your own Gmail as a **test user**.
   - Then click **Publish app** so the status says **In production**.
     This matters: while it says "Testing", Google makes you log in again every 7 days.
     You don't need Google to review the app. It only asks for access to files it creates.
5. Go to **APIs & Services → Credentials → Create credentials → OAuth client ID**.
   - Application type: **Desktop app**.
   - Click **Download JSON**, rename the file to `credentials.json`,
     and put it in this folder.

### Step 2. ESPN: copy your two login cookies (your league is private)

1. In Chrome, go to https://fantasy.espn.com and make sure you're logged in.
2. Press **Cmd + Option + I** to open Developer Tools.
3. Click the **Application** tab → **Cookies** (left side) → `https://fantasy.espn.com`.
4. Find these two rows and copy their **Value**:
   - `espn_s2` (a long string)
   - `SWID` (looks like `{ABCD-1234-...}`; include the curly brackets)
5. Copy `config.example.json` to `config.json` (`cp config.example.json config.json`),
   fill in your league ID (the number after `leagueId=` in your ESPN league link)
   and team name, and paste the cookies in:
   ```json
   "espn_s2": "paste espn_s2 here",
   "swid": "{paste-SWID-here}"
   ```
   Keep these private. Anyone with them can open your ESPN account.

### Step 3. Install and schedule

Open **Terminal** and run:

```bash
cd ~/Downloads/Projects/NBAFantasy26
./install.sh
```

This will:
1. Install the Python packages it needs.
2. Open your browser to log in to Google. Choose your account and click **Allow**.
   If you see "Google hasn't verified this app", click **Advanced → Go to NBAFantasy26**.
3. Run once. The Terminal will print the link to your new Google Sheet.
4. Schedule the daily 8:00 AM run.

### Step 4. Let the scheduled run read this folder

macOS protects the Downloads folder from programs that run in the background,
so the 8:00 AM run can fail even though running it by hand works.

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Click **+**, press **Cmd + Shift + G**, and paste the Python path that `install.sh`
   printed ("Using Python: ..."). Click **Open** and make sure it is switched on.

To test the scheduled version right away:

```bash
launchctl kickstart gui/$(id -u)/com.renke.fantasyupdate
cat ~/Downloads/Projects/NBAFantasy26/update.log
```

The last line should say "Updated Google Sheet".

---

## Everyday use

- **Open the sheet:** use the link in `update.log` (the ID is also in `sheet_id.txt`).
- **Run it now:** `python3 fantasy_update.py`
- **Check what happened:** `cat update.log`
- **Stop the daily run:** `./uninstall.sh`

Each update replaces the whole sheet, so don't type your own notes into it.
Put notes in a separate Google Sheet.

## Safety checks during each sync

- **Someone edited the sheet:** the current sheet is downloaded to `backups/` first
  (last 20 kept), then replaced. The log says who made the last change.
- **Sheet deleted or moved to Trash:** a new sheet is made and you get a Mac notification
  to re-share the new link.
- **You lost edit access:** the sync stops and tells you. Nothing is changed.
- **ESPN data looks wrong or ESPN is down:** the sheet is left as it was.
- **Temporary network / Google errors:** tried up to 3 times before giving up.
- **Two runs at once:** the second one waits its turn (stops with a message).
- **Edit warning:** each tab gets a pop-up for anyone who tries to edit it, saying the sheet
  is auto-updated. This needs the **Google Sheets API** turned on in your Google Cloud
  project (APIs & Services → Library → Google Sheets API → Enable; free).
- Any failure shows a Mac notification and is written to `update.log`.

## If something breaks

| What `update.log` says | Fix |
|---|---|
| `Google login missing or expired` | Run `python3 fantasy_update.py --login` |
| An ESPN error like `401` / `ESPNAccessDenied` | Your ESPN cookies expired. Repeat Step 2. |
| `Operation not permitted` | Redo Step 4 (Full Disk Access). |
| `No matchups found` | Check `league_id` and `season_year` in `config.json`. |
| `can no longer edit the Google Sheet` | Someone changed sharing. Make sure your account is still the owner/editor. |
| `ESPN data looks wrong` | Usually ESPN is mid-update. It will try again next run. |
| `Another update is already running` | Wait a few minutes. If it keeps happening, delete `.update.lock`. |
| `could not add the edit warning` | Turn on the Google Sheets API (see Safety checks). Data still updated. |

## Files in this folder

| File | What it is |
|---|---|
| `fantasy_update.py` | The script |
| `config.example.json` | Template for `config.json` (safe to share) |
| `config.json` | League ID, season, your team name, ESPN cookies (private, not in git) |
| `credentials.json` | Your Google app file from Step 1 (you add this) |
| `token.json` | Your saved Google login (created on first run; keep private) |
| `sheet_id.txt` | Which Google Sheet to update (created on first run) |
| `The_Boys_League_Stats.xlsx` | Local backup copy of the sheet |
| `update.log` | Record of each daily run |
| `install.sh` / `uninstall.sh` | Turn the daily run on / off |

## Privacy

`config.json`, `credentials.json`, `token.json`, `sheet_id.txt`, `sync_state.json`,
`update.log`, `backups/` and all `.xlsx` files are listed in `.gitignore` and are never
committed. Before every push, run `git status` and make sure none of them appear.
