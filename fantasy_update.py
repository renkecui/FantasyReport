#!/usr/bin/env python3
"""
NBAFantasy26: pull ESPN fantasy basketball league data and update a Google Sheet.

  python3 fantasy_update.py           # normal run (what the 8am schedule does)
  python3 fantasy_update.py --login   # sign in to Google again (first time, or if the login expired)
  python3 fantasy_update.py --excel   # only save a local .xlsx copy, skip Google

See README.md for setup.
"""
import json
import os
import sys
from datetime import datetime

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]

# ---------------------------------------------------------------- fetch
def fetch(cfg):
    from espn_api.basketball import League

    kw = {"league_id": int(cfg["league_id"]), "year": int(cfg["season_year"])}
    if cfg.get("espn_s2") and cfg.get("swid"):
        kw["espn_s2"] = cfg["espn_s2"]
        kw["swid"] = cfg["swid"]
    league = League(**kw)

    names = {t.team_id: t.team_name.strip() for t in league.teams}
    current = league.currentMatchupPeriod
    weeks = []
    for mp in range(1, current + 1):
        winners = {}
        for m in league.scoreboard(mp):
            if not m.home_team or not m.away_team:
                continue
            h, a = m.home_team.team_id, m.away_team.team_id
            winners[(h, a)] = m.winner
        rows = []
        for b in league.box_scores(matchup_period=mp):
            h, a = b.home_team, b.away_team
            h = getattr(h, "team_id", h)
            a = getattr(a, "team_id", a)
            if not h or not a:
                continue
            win = winners.get((h, a), b.winner)
            final = win in ("HOME", "AWAY", "TIE") and mp < current
            for side, me, opp in (("home", h, a), ("away", a, h)):
                stats = getattr(b, f"{side}_stats") or {}
                if final:
                    if win == "TIE":
                        res = "T"
                    else:
                        res = "W" if win.lower() == side else "L"
                else:
                    res = "Live"
                rows.append({
                    "team": names[me], "opp": names[opp],
                    "w": getattr(b, f"{side}_wins"), "l": getattr(b, f"{side}_losses"),
                    "t": getattr(b, f"{side}_ties"), "result": res,
                    "stats": {c: (stats.get(c) or {}).get("value", 0) for c in CATS},
                })
        weeks.append({"week": mp, "final": mp < current, "rows": rows})

    my = cfg.get("my_team_name", "").strip()
    my_team = next((t for t in league.teams if t.team_name.strip() == my), None)
    roster = []
    if my_team:
        key = f"{cfg['season_year']}_total"
        for p in my_team.roster:
            avg = (p.stats.get(key) or {}).get("avg") or {}
            roster.append({
                "slot": p.lineupSlot, "name": p.name, "team": p.proTeam,
                "pos": ", ".join(s for s in p.eligibleSlots if s in ("PG", "SG", "SF", "PF", "C")),
                "status": {"DAY_TO_DAY": "DTD", "OUT": "O", "INJURY_RESERVE": "IR", "SUSPENSION": "SUSP"}.get(
                    p.injuryStatus, p.injuryStatus) if p.injuryStatus not in (None, "ACTIVE", "NORMAL") else "",
                **{k: avg.get(k, 0) for k in ("MIN", "FGM", "FGA", "FTM", "FTA", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS")},
            })
    order = [names[t.team_id] for t in sorted(league.teams, key=lambda t: t.team_id)]
    return {"teams": order, "weeks": weeks, "roster": roster, "my_team": my}

# ---------------------------------------------------------------- styling helpers
F = "Arial"
NAVY, MID, GREY, PURP, ORNG = "1F3864", "2F5597", "595959", "7030A0", "C55A11"
PALETTE = ["DDEBF7", "FFF2CC", "EDEDED", "E4DFEC", "FCE4D6", "EFE6DA",
           "D9E1F2", "FFE699", "D0CECE", "CCC0DA", "F8CBAD", "E2D5C3"]
fill = lambda c: PatternFill("solid", start_color=c, end_color=c)
thin = Side(style="thin", color="D9D9D9")
thick = Side(style="medium", color=NAVY)
cen = Alignment(horizontal="center", vertical="center")
left = Alignment(horizontal="left", vertical="center", indent=1)
blue = Font(name=F, size=10, color="0000FF")


def banner(ws, n, title, sub):
    ws.sheet_view.showGridLines = False
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n)
    a = ws.cell(1, 1, value=title)
    a.font = Font(name=F, bold=True, size=16, color="FFFFFF"); a.alignment = left
    for c in range(1, n + 1):
        ws.cell(1, c).fill = fill(NAVY)
    b = ws.cell(2, 1, value=sub)
    b.font = Font(name=F, italic=True, size=9, color=GREY)
    b.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[1].height = 34
    ws.row_dimensions[2].height = 30


def groups(ws, spec):
    ws.row_dimensions[3].height = 20
    for s, e, txt, col in spec:
        ws.merge_cells(start_row=3, start_column=s, end_row=3, end_column=e)
        c = ws.cell(3, s, value=txt)
        c.font = Font(name=F, bold=True, size=10, color="FFFFFF"); c.alignment = cen
        for k in range(s, e + 1):
            ws.cell(3, k).fill = fill(col)
            ws.cell(3, k).border = Border(left=Side(style="thin", color="FFFFFF"), right=Side(style="thin", color="FFFFFF"))


def header(ws, heads):
    ws.row_dimensions[4].height = 30
    for i, h in enumerate(heads, 1):
        x = ws.cell(4, i, value=h)
        x.font = Font(name=F, bold=True, size=10, color=NAVY); x.fill = fill("D6DCE4")
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        x.border = Border(bottom=thick, top=thin, left=thin, right=thin)


def scale(ws, rng, low_good=True):
    a, b = ("63BE7B", "F8696B") if low_good else ("F8696B", "63BE7B")
    ws.conditional_formatting.add(rng, ColorScaleRule(
        start_type="min", start_color=a, mid_type="percentile", mid_value=50,
        mid_color="FFEB84", end_type="max", end_color=b))


def paint(ws, r1, r2, n, seps, teamc, colors, week_sep=False):
    for r in range(r1, r2 + 1):
        tc = colors.get(ws.cell(r, teamc).value, "FFFFFF")
        ws.row_dimensions[r].height = 21
        for c in range(1, n + 1):
            x = ws.cell(r, c)
            x.fill = fill(tc)
            if x.alignment.horizontal is None:
                x.alignment = cen
            bb = thick if (week_sep and r < r2 and ws.cell(r, 1).value != ws.cell(r + 1, 1).value) else thin
            x.border = Border(left=thick if c in seps else thin, right=thin, top=thin, bottom=bb)

# ---------------------------------------------------------------- workbook
def build(data, path, overrides=None):
    overrides = overrides or {}
    teams = data["teams"]
    my = data.get("my_team")
    if my in teams:
        teams = [my] + [t for t in teams if t != my]
    colors = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(teams)}
    stamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
    wb = Workbook()

    # ---- Weekly Stats
    ws = wb.active
    ws.title = "Weekly Stats"
    N = 27
    heads = ["Week", "Team", "Opponent", "Cat W", "Cat L", "Cat T", "Result",
             "Avg Rank", "Overall Rank"] + CATS + CATS
    rows = [(wk, row) for wk in data["weeks"] for row in wk["rows"]]
    first = 5
    last = first + len(rows) - 1
    blocks = []
    for i, (wk, row) in enumerate(rows):
        r = first + i
        if not blocks or blocks[-1][0] != wk["week"]:
            blocks.append([wk["week"], r, r])
        blocks[-1][2] = r
        for c, v in enumerate([wk["week"], row["team"], row["opp"], row["w"], row["l"], row["t"]], 1):
            ws.cell(r, c, value=v).font = blue
        res = overrides.get((wk["week"], row["team"]), row["result"])
        g = ws.cell(r, 7, value=res)
        g.font = Font(name=F, size=10, bold=True)
        if res in ("W", "L") and row["w"] == row["l"]:
            g.comment = Comment("Category tie; the league tiebreaker decided this result.", "Claude")
        ws.cell(r, 8, value=f"=AVERAGE(S{r}:AA{r})").number_format = "0.00"
        ws.cell(r, 8).font = Font(name=F, size=10)
        ws.cell(r, 9, value=f'=COUNTIFS($A${first}:$A${last},$A{r},$H${first}:$H${last},"<"&H{r})+1').font = Font(name=F, size=11, bold=True)
        for j, cat in enumerate(CATS):
            x = ws.cell(r, 10 + j, value=row["stats"][cat])
            x.font = blue
            x.number_format = ".0000" if j < 2 else "#,##0"
        for j, cat in enumerate(CATS):
            sc = L(10 + j)
            op = "<" if cat == "TO" else ">"
            ws.cell(r, 19 + j, value=f'=COUNTIFS($A${first}:$A${last},$A{r},{sc}${first}:{sc}${last},"{op}"&{sc}{r})+1').font = Font(name=F, size=10, bold=True)
        ws.cell(r, 2).font = Font(name=F, size=10, bold=True, color="0000FF")
        ws.cell(r, 2).alignment = left
        ws.cell(r, 3).alignment = left
    live = [w["week"] for w in data["weeks"] if not w["final"]]
    live_txt = f" · Week {live[0]} is still in progress (Result = Live)" if live else ""
    banner(ws, N, "🏀  THE BOYS LEAGUE  ·  Weekly Matchups",
           f"Updated {stamp} from ESPN · Ranks: 1 = best that week (TO: fewest is best) · "
           f"Overall = week rank by average of the 9 category ranks (lower avg = better){live_txt}")
    groups(ws, [(1, 7, "MATCHUP", NAVY), (8, 9, "OVERALL", ORNG),
                (10, 18, "CATEGORY STATS", MID), (19, 27, "WEEKLY RANK  (1 = best)", PURP)])
    header(ws, heads)
    if rows:
        paint(ws, first, last, N, {8, 10, 19}, 2, colors, week_sep=True)
        for _, a, b in blocks:
            scale(ws, f"S{a}:AA{b}")
            scale(ws, f"I{a}:I{b}")
        ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(operator="equal", formula=['"W"'], fill=fill("C6EFCE"), font=Font(name=F, bold=True, color="006100")))
        ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(operator="equal", formula=['"L"'], fill=fill("FFC7CE"), font=Font(name=F, bold=True, color="9C0006")))
    for i, w in enumerate([7, 24, 24, 7, 7, 7, 8, 9, 10] + [8.5] * 18, 1):
        ws.column_dimensions[L(i)].width = w
    ws.freeze_panes = "D5"

    # ---- Season Totals
    t = wb.create_sheet("Season Totals", 0)
    N = 26
    S = "'Weekly Stats'!"
    rng = lambda c: f"{S}${c}${first}:${c}${last}"
    th = ["Team", "Matchup W", "Matchup L", "Matchup T", "Record", "Cat W", "Cat L", "Cat T"] + CATS + CATS
    tl = 4 + len(teams)
    for k, tm in enumerate(teams):
        r = 5 + k
        t.cell(r, 1, value=tm).font = Font(name=F, size=10, bold=True, color="0000FF")
        t.cell(r, 1).alignment = left
        for c, res in ((2, "W"), (3, "L"), (4, "T")):
            t.cell(r, c, value=f'=COUNTIFS({rng("B")},$A{r},{rng("G")},"{res}")')
        t.cell(r, 5, value=f'=B{r}&"-"&C{r}&"-"&D{r}').font = Font(name=F, size=11, bold=True)
        for c, col in zip((6, 7, 8), ("D", "E", "F")):
            t.cell(r, c, value=f'=SUMIFS({rng(col)},{rng("B")},$A{r})')
        for j in range(9):
            col = L(10 + j)
            fn = "AVERAGEIFS" if j < 2 else "SUMIFS"
            x = t.cell(r, 9 + j, value=f'={fn}({rng(col)},{rng("B")},$A{r})')
            x.number_format = ".0000" if j < 2 else "#,##0"
        for j in range(9):
            sc = L(9 + j)
            t.cell(r, 18 + j, value=f'=RANK({sc}{r},${sc}$5:${sc}${tl},{1 if CATS[j] == "TO" else 0})').font = Font(name=F, size=10, bold=True)
        for c in list(range(2, 5)) + list(range(6, 18)):
            t.cell(r, c).font = Font(name=F, size=10)
    nweeks = len(data["weeks"])
    banner(t, N, f"🏆  SEASON TOTALS  ·  Weeks 1-{nweeks}",
           f"Updated {stamp} from ESPN · Counting stats are summed; FG% and FT% are averages of weekly %. "
           f"Record counts finished weeks only; stats include any week in progress. Rank 1 = best (TO: fewest is best).")
    groups(t, [(1, 8, "RECORD", NAVY), (9, 17, "SEASON STATS", MID), (18, 26, "LEAGUE RANK  (1 = best)", PURP)])
    header(t, th)
    paint(t, 5, tl, N, {9, 18}, 1, colors)
    for r in range(5, tl + 1):
        t.row_dimensions[r].height = 24
    scale(t, f"R5:Z{tl}")
    for i, w in enumerate([24, 9, 9, 9, 10, 7, 7, 7] + [9] * 18, 1):
        t.column_dimensions[L(i)].width = w
    t.freeze_panes = "B5"

    # ---- Roster
    p = wb.create_sheet(f"{my or 'My'} Roster"[:31])
    ph = ["Slot", "Player", "NBA Team", "Positions", "Status", "MIN", "FGM", "FGA", "FG%", "FTM", "FTA", "FT%",
          "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
    N = len(ph)
    order = {"PG": 0, "SG": 1, "SF": 2, "PF": 3, "C": 4, "G": 5, "F": 6, "UT": 7, "UTIL": 7, "BE": 8, "Bench": 8, "IR": 9}
    roster = sorted(data.get("roster", []), key=lambda x: order.get(x["slot"], 8))
    for k, pl in enumerate(roster):
        r = 5 + k
        slot = {"BE": "Bench", "UT": "UTIL"}.get(pl["slot"], pl["slot"])
        vals = [slot, pl["name"], pl["team"], pl["pos"], pl["status"], pl["MIN"], pl["FGM"], pl["FGA"], None,
                pl["FTM"], pl["FTA"], None, pl["3PM"], pl["REB"], pl["AST"], pl["STL"], pl["BLK"], pl["TO"], pl["PTS"]]
        for c, v in enumerate(vals, 1):
            x = p.cell(r, c, value=v)
            x.font = Font(name=F, size=10, color="0000FF")
            x.alignment = cen
            if isinstance(v, (int, float)) and c >= 6:
                x.number_format = "0.0"
        p.cell(r, 9, value=f"=IFERROR(G{r}/H{r},0)").number_format = ".000"
        p.cell(r, 12, value=f"=IFERROR(J{r}/K{r},0)").number_format = ".000"
        for c in (9, 12):
            p.cell(r, c).font = Font(name=F, size=10); p.cell(r, c).alignment = cen
        p.cell(r, 1).font = Font(name=F, size=10, bold=True, color=NAVY)
        p.cell(r, 2).font = Font(name=F, size=10, bold=True, color="0000FF")
        p.cell(r, 2).alignment = left
        p.cell(r, 5).font = Font(name=F, size=10, bold=True, color="C00000")
        bg = "FFFFFF" if k % 2 == 0 else "F7F9FC"
        for c in range(1, N + 1):
            p.cell(r, c).fill = fill(bg)
            p.cell(r, c).border = Border(left=thick if c in (6, 13) else thin, right=thin, top=thin, bottom=thin)
        p.row_dimensions[r].height = 21
    pl_last = 4 + len(roster)
    banner(p, N, f"📋  {my or 'My'} ROSTER  ·  Season Averages",
           f"Updated {stamp} from ESPN · FG% and FT% are formulas (made ÷ attempted) · "
           f"FG%, FT% and TO colored: green = best on team, red = worst")
    groups(p, [(1, 5, "PLAYER", NAVY), (6, 12, "SHOOTING", MID), (13, 19, "PER GAME", "2E75B6")])
    header(p, ph)
    if roster:
        scale(p, f"I5:I{pl_last}", low_good=False)
        scale(p, f"L5:L{pl_last}", low_good=False)
        scale(p, f"R5:R{pl_last}")
    for i, w in enumerate([8, 22, 9, 11, 9] + [7.5] * 14, 1):
        p.column_dimensions[L(i)].width = w
    p.freeze_panes = "C5"

    for sh, col in ((t, PURP), (ws, MID), (p, "00873C")):
        sh.sheet_properties.tabColor = col
        sh.page_setup.orientation = "landscape"
        sh.sheet_properties.pageSetUpPr.fitToPage = True
        sh.page_setup.fitToHeight = 0
    wb.active = 0
    wb.save(path)


# ---------------------------------------------------------------- Google Sheets
SCOPES = ["https://www.googleapis.com/auth/drive.file"]  # only files this script creates
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
GSHEET = "application/vnd.google-apps.spreadsheet"
TOKEN = os.path.join(HERE, "token.json")
CREDS = os.path.join(HERE, "credentials.json")
SHEET_ID_FILE = os.path.join(HERE, "sheet_id.txt")
STATE_FILE = os.path.join(HERE, "sync_state.json")
BACKUP_DIR = os.path.join(HERE, "backups")
LOCK_FILE = os.path.join(HERE, ".update.lock")
KEEP_BACKUPS = 20


class SyncError(Exception):
    """A problem that should stop the run without touching the Google Sheet."""


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}", flush=True)


def notify(title, msg):
    """Show a macOS notification so a failed 8am run doesn't go unnoticed."""
    try:
        import subprocess
        safe = msg.replace('"', "'")[:200]
        subprocess.run(["osascript", "-e", f'display notification "{safe}" with title "{title}"'],
                       timeout=10, capture_output=True)
    except Exception:
        pass


def retry(what, fn, tries=3, wait=5):
    """Run fn(); on a temporary error (network, Google 429/5xx) wait and try again."""
    import time
    for n in range(1, tries + 1):
        try:
            return fn()
        except Exception as e:
            status = getattr(getattr(e, "resp", None), "status", None)
            permanent = status in (400, 401, 403, 404)
            if permanent or n == tries:
                raise
            log(f"{what} failed (try {n}/{tries}): {e}. Retrying in {wait * n}s...")
            time.sleep(wait * n)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def google_creds(interactive):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if os.path.exists(TOKEN):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        except Exception as e:
            log(f"token.json could not be read ({e}).")
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            open(TOKEN, "w").write(creds.to_json())
            return creds
        except Exception as e:
            log(f"Google login refresh failed: {e}")
    if not interactive:
        raise SyncError("Google login missing or expired. In Terminal run:  python3 fantasy_update.py --login")
    if not os.path.exists(CREDS):
        raise SyncError("credentials.json not found. See README.md step 1.")
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES).run_local_server(port=0)
    open(TOKEN, "w").write(creds.to_json())
    os.chmod(TOKEN, 0o600)
    return creds


def validate(data, cfg):
    """Make sure the ESPN data looks complete before it replaces anything."""
    problems = []
    teams = data.get("teams") or []
    if len(teams) < 2:
        problems.append(f"only {len(teams)} teams came back from ESPN")
    for wk in data["weeks"]:
        if wk["final"] and len(wk["rows"]) != len(teams):
            problems.append(f"week {wk['week']} has {len(wk['rows'])} rows for {len(teams)} teams")
        for row in wk["rows"]:
            missing = [c for c in CATS if row["stats"].get(c) is None]
            if missing:
                problems.append(f"week {wk['week']} {row['team']} is missing {', '.join(missing)}")
            if wk["final"] and row["w"] + row["l"] + row["t"] != len(CATS):
                problems.append(f"week {wk['week']} {row['team']} category score doesn't add up to 9")
    my = cfg.get("my_team_name", "").strip()
    if my and my not in teams:
        problems.append(f"team '{my}' not found (ESPN names: {', '.join(teams)}); check my_team_name in config.json")
    if problems:
        raise SyncError("ESPN data looks wrong, Google Sheet left unchanged: " + "; ".join(problems[:5]))


def backup_sheet(drive, sheet_id, reason):
    """Download the current Google Sheet as .xlsx before it gets replaced."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, f"sheet_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx")
    buf = io.BytesIO()
    req = drive.files().export_media(fileId=sheet_id, mimeType=XLSX)
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    old = sorted(p for p in os.listdir(BACKUP_DIR) if p.endswith(".xlsx"))
    for p in old[:-KEEP_BACKUPS]:
        try:
            os.remove(os.path.join(BACKUP_DIR, p))
        except OSError:
            pass
    log(f"Backed up current Google Sheet ({reason}) to backups/{os.path.basename(path)}")
    return path


def check_sheet(drive, sheet_id, state):
    """
    Look at the live Google Sheet before overwriting it.
    Returns (ok_to_update, warnings). ok_to_update=False means make a new sheet instead.
    """
    from googleapiclient.errors import HttpError

    warnings = []
    try:
        meta = retry("Reading sheet info", lambda: drive.files().get(
            fileId=sheet_id,
            fields="id,name,mimeType,trashed,modifiedTime,capabilities/canEdit,"
                   "lastModifyingUser(displayName,emailAddress,me)").execute())
    except HttpError as e:
        status = getattr(e.resp, "status", None)
        if status == 404:
            warnings.append("The Google Sheet was deleted or this script lost access to it. Making a new one.")
            return False, warnings, None
        raise
    if meta.get("trashed"):
        warnings.append(f"The Google Sheet '{meta.get('name')}' is in the Trash. Making a new one "
                        f"(restore the old one from Drive's Trash if you need it).")
        return False, warnings, meta
    if meta.get("mimeType") != GSHEET:
        warnings.append("The saved file is no longer a Google Sheet. Making a new one.")
        return False, warnings, meta
    if not meta.get("capabilities", {}).get("canEdit", False):
        raise SyncError("Your account can no longer edit the Google Sheet. Check its sharing settings.")

    who = meta.get("lastModifyingUser") or {}
    changed_since_sync = state.get("last_modified") and meta.get("modifiedTime") != state.get("last_modified")
    if changed_since_sync or not who.get("me", True):
        name = who.get("displayName") or who.get("emailAddress") or "someone"
        warnings.append(f"The Google Sheet was edited since the last sync (last change by {name}). "
                        f"Those edits are saved in the backups folder and will be replaced.")
        meta["_edited"] = True
    return True, warnings, meta


def protect_tabs(creds, sheet_id):
    """
    Put a 'warning only' protection on every tab, so anyone editing gets a pop-up
    saying the sheet is auto-updated. Best effort: a failure here never fails the sync.
    """
    try:
        from googleapiclient.discovery import build as gbuild
        sheets = gbuild("sheets", "v4", credentials=creds, cache_discovery=False)
        info = sheets.spreadsheets().get(spreadsheetId=sheet_id, fields="sheets(properties(sheetId),protectedRanges(protectedRangeId))").execute()
        reqs = []
        for sh in info.get("sheets", []):
            if sh.get("protectedRanges"):
                continue
            reqs.append({"addProtectedRange": {"protectedRange": {
                "range": {"sheetId": sh["properties"]["sheetId"]},
                "description": "Auto-updated from ESPN every day at 8 AM. Edits here will be replaced.",
                "warningOnly": True}}})
        if reqs:
            sheets.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()
    except Exception as e:
        log(f"Note: could not add the edit warning to the tabs ({e}). The data still updated.")


def push_to_sheets(xlsx_path, title, interactive):
    from googleapiclient.discovery import build as gbuild
    from googleapiclient.http import MediaFileUpload

    creds = google_creds(interactive)
    drive = gbuild("drive", "v3", credentials=creds, cache_discovery=False)
    state = load_state()
    sheet_id = open(SHEET_ID_FILE).read().strip() if os.path.exists(SHEET_ID_FILE) else ""
    warnings = []
    created = False

    ok = False
    if sheet_id:
        ok, warnings, meta = check_sheet(drive, sheet_id, state)
        for w in warnings:
            log("WARNING: " + w)
        if ok and meta and meta.get("_edited"):
            try:
                backup_sheet(drive, sheet_id, "edited by someone since last sync")
            except Exception as e:
                # Never wipe other people's edits without a copy.
                raise SyncError(f"Sheet was edited since last sync but the backup failed ({e}). "
                                f"Left the sheet unchanged so nothing is lost.")

    def upload_update():
        media = MediaFileUpload(xlsx_path, mimetype=XLSX, resumable=False)
        return drive.files().update(fileId=sheet_id, media_body=media,
                                    fields="id,modifiedTime").execute()

    def upload_create():
        media = MediaFileUpload(xlsx_path, mimetype=XLSX, resumable=False)
        return drive.files().create(body={"name": title, "mimeType": GSHEET}, media_body=media,
                                    fields="id,modifiedTime").execute()

    if ok:
        res = retry("Updating Google Sheet", upload_update)
    else:
        res = retry("Creating Google Sheet", upload_create)
        sheet_id = res["id"]
        open(SHEET_ID_FILE, "w").write(sheet_id)
        created = True
        warnings.append("A NEW Google Sheet link was created. Re-share it with your league.")

    protect_tabs(creds, sheet_id)
    # Read back the final modified time (after protections) so the next run can tell if anyone edited.
    try:
        final = drive.files().get(fileId=sheet_id, fields="modifiedTime").execute()
        state["last_modified"] = final.get("modifiedTime") or res.get("modifiedTime")
    except Exception:
        state["last_modified"] = res.get("modifiedTime")
    state["last_sync"] = datetime.now().isoformat(timespec="seconds")
    state["sheet_id"] = sheet_id
    save_state(state)
    return sheet_id, created, warnings


class RunLock:
    """Stops two updates from running at the same time (e.g. 8am run + manual run)."""

    def __enter__(self):
        import time
        if os.path.exists(LOCK_FILE) and time.time() - os.path.getmtime(LOCK_FILE) < 30 * 60:
            raise SyncError("Another update is already running. Try again in a few minutes.")
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return self

    def __exit__(self, *exc):
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass


def run(args):
    with open(os.path.join(HERE, "config.json")) as f:
        cfg = json.load(f)
    if "--login" in args:
        google_creds(interactive=True)
        log("Google login saved.")
    try:
        data = retry("Getting ESPN data", lambda: fetch(cfg))
    except SyncError:
        raise
    except Exception as e:
        text = str(e)
        if "401" in text or "Access" in text or "private" in text.lower():
            raise SyncError(f"ESPN refused the request ({e}). Your ESPN cookies probably expired; "
                            f"update espn_s2 and swid in config.json (README Step 2).")
        raise SyncError(f"Could not get ESPN data ({e}). Google Sheet left unchanged.")
    if not data["weeks"]:
        raise SyncError("No matchups found. Check league_id and season_year in config.json.")
    validate(data, cfg)

    local = os.path.join(HERE, "The_Boys_League_Stats.xlsx")
    tmp = local + ".tmp.xlsx"
    build(data, tmp)
    os.replace(tmp, local)  # local copy, always kept up to date
    msg = f"ESPN data OK: {len(data['weeks'])} weeks."
    if "--excel" not in args:
        sid, new, warnings = push_to_sheets(local, cfg.get("sheet_title", "The Boys League Stats"),
                                            interactive="--login" in args)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
        msg += f" {'Created' if new else 'Updated'} Google Sheet: {url}"
        if warnings:
            notify("NBAFantasy26 sync", warnings[-1])
    log(msg)


def main():
    args = set(sys.argv[1:])
    try:
        with RunLock():
            run(args)
    except SyncError as e:
        log("ERROR: " + str(e))
        notify("NBAFantasy26 sync failed", str(e))
        sys.exit(1)
    except Exception as e:
        import traceback
        log(f"ERROR: unexpected problem: {e}")
        traceback.print_exc()
        notify("NBAFantasy26 sync failed", f"Unexpected error: {e}. See update.log.")
        sys.exit(1)


if __name__ == "__main__":
    main()
