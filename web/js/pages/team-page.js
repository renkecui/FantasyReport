import { SortableTable } from "../components/sortable-table.js";
import { Widgets } from "../components/widgets.js";
import { Page } from "./page.js";
import { Session } from "../state/session.js";
import { Dom } from "../util/dom.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

const el = Dom.el;

/** #/team/<name>: one team's roster with player stats, and its week-by-week results. */
export class TeamPage extends Page {
  get title() { return "Teams"; }

  constructor(param) {
    super(param);
    const names = this.league.teamNames;
    const session = Session.instance();
    this.name = names.includes(param) ? param : (session.loggedIn && names.includes(session.team) ? session.team : names[0]);
    this.row = this.league.seasonRow(this.name);
    this.players = this.league.roster(this.name);
    this.n = this.league.season.length;
    this.weekIndex = this.league.weeks.length - 1;  // the weekly player stats open on the latest week
    SortableTable.resetSort("roster");   // each team opens in lineup order
    SortableTable.resetSort("history");
  }

  picker() {
    return el("nav", { class: "team-picker", "aria-label": "Teams" }, this.league.teamNames.map(t =>
      el("a", { href: Widgets.teamHref(t), "aria-current": t === this.name ? "page" : null, style: Widgets.teamStyle(t) },
        Widgets.dot(t), t + (Session.instance().isMine(t) ? " (you)" : ""))));
  }

  summary() {
    const r = this.row;
    if (!r) return null;
    const tile = (label, value) => el("div", { class: "stat-tile" },
      el("div", { class: "label" }, label), el("div", { class: "value" }, value));
    return el("div", { class: "team-summary" },
      tile("Record", r.record),
      tile("Standing", `${this.league.place(r)} of ${this.n}`),
      tile("Category record", Format.score(r)),
      tile("Avg league rank", Format.two(r.avg_rank)),
      tile("Injured / out", String(this.players.filter(p => p.status).length)));
  }

  rankChips() {
    const r = this.row;
    if (!r) return null;
    return el("div", { class: "rank-chips", "aria-label": "League rank per category" },
      this.league.categories.map(c => el("div", {
        class: "rank-chip tint", style: { "--h": RankColor.hue(RankColor.ofRank(r.ranks[c], this.n)) },
        title: `${c}: ${Format.category(c, r.stats[c])} (rank ${r.ranks[c]} of ${this.n})`,
      }, el("span", { class: "cat" }, c), el("span", { class: "rk" }, "#" + r.ranks[c]))));
  }

  /** Whether league.json has players' weekly games (older files don't). */
  get hasPlayerWeeks() {
    return this.league.weeks.length > 0 && this.players.some(p => p.weeks && Object.keys(p.weeks).length);
  }

  get weekly() { return this.hasPlayerWeeks && this.prefs.playerStats === "week"; }
  get week() { return this.league.weeks[this.weekIndex]; }

  /** A player's games in the shown week: { games, stats } (per game or totals), or null without a game. */
  weekOf(p) {
    const w = p.weeks?.[this.week.number];
    if (!w || !w.games) return null;
    if (this.prefs.playerWeekStats === "total") return { games: w.games, stats: w.totals };
    const stats = {};
    for (const [k, v] of Object.entries(w.totals)) stats[k] = Format.PCT.has(k) ? v : v / w.games;
    return { games: w.games, stats };
  }

  /** The stats shown for a player: season averages, or the week's (null when he didn't play). */
  statsOf(p) { return this.weekly ? this.weekOf(p)?.stats ?? null : p.stats; }

  /** Roster: every stat but MIN tinted best→worst within the team (TO: fewest is best). */
  rosterTable() {
    const players = this.players;
    if (!players.length) return el("p", { class: "state" }, "No roster data.");
    const weekly = this.weekly, totals = weekly && this.prefs.playerWeekStats === "total";
    const statGroup = totals ? "Totals" : "Per game";
    const stat = (key, group, { pct = false, tint = true, lowerBetter = false } = {}) => {
      const of = p => this.statsOf(p)?.[key] ?? null;
      const shown = players.map(of).filter(v => v != null);
      return {
        key, label: key, group, dir: lowerBetter ? "asc" : "desc",
        // players without a game that week sort last on the first click
        value: p => of(p) ?? (lowerBetter ? Infinity : -Infinity),
        cell: p => (pct ? Format.pct(of(p)) : totals ? Format.int(of(p)) : Format.one(of(p))),
        tint: tint ? p => (of(p) == null ? null : RankColor.within(of(p), shown, lowerBetter)) : null,
      };
    };
    const slotGroup = s => (s === "IR" ? 2 : s === "Bench" ? 1 : 0);
    const columns = [
      { key: "slot", label: "Slot", cls: "slot", resetsSort: true, title: "Back to slot order",
        cell: p => p.slot },
      { key: "name", label: "Player", cls: "name", group: "Player", sortable: false,
        cell: p => el("span", {}, p.name, p.status ? el("span", { class: "badge status" }, p.status) : null) },
      { key: "nba", label: "Team", cls: "nba-team", group: "Player", sortable: false, value: p => p.nba_team },
      { key: "pos", label: "Pos", group: "Player", sortable: false, cell: p => p.positions || "–" },
      weekly ? { key: "gp", label: "GP", group: "Player", dir: "desc", title: "Games played that week",
        value: p => this.weekOf(p)?.games ?? 0, cell: p => String(this.weekOf(p)?.games ?? 0) } : null,
      stat("MIN", "Shooting", { tint: false }), stat("FGM", "Shooting"), stat("FGA", "Shooting"),
      stat("FG%", "Shooting", { pct: true }),
      stat("FTM", "Shooting"), stat("FTA", "Shooting"),
      stat("FT%", "Shooting", { pct: true }),
      stat("3PM", statGroup), stat("REB", statGroup), stat("AST", statGroup),
      stat("STL", statGroup), stat("BLK", statGroup),
      stat("TO", statGroup, { lowerBetter: true }), stat("PTS", statGroup),
    ].filter(Boolean);
    const firstIR = players.findIndex(p => p.slot === "IR");
    return new SortableTable(columns, {
      id: "roster", rows: players, defaultSort: null, stickyName: true,
      pinned: p => p.slot === "IR",  // IR players stay at the bottom, whatever the sort
      rowClass: (p, i, sorted) => [
        sorted ? (i === firstIR && i > 0 ? "divider" : null)
          : (i > 0 && slotGroup(p.slot) !== slotGroup(players[i - 1].slot) ? "divider" : null),
        weekly && !this.weekOf(p) ? "no-games" : null,
      ].filter(Boolean).join(" ") || null,
    }).render();
  }

  /** The Season / Weekly switch, and for a week its picker and Per game / Total switch. */
  rosterControls(redraw) {
    if (!this.hasPlayerWeeks) return null;
    const weeks = this.league.weeks;
    return el("div", { class: "controls roster-controls" },
      Widgets.playerStatsToggle(redraw),
      this.weekly ? Widgets.weekPicker(weeks, this.weekIndex, i => { this.weekIndex = i; redraw(); }) : null,
      this.weekly ? Widgets.playerWeekStatsToggle(redraw) : null);
  }

  rosterNote() {
    if (!this.weekly) return "Current roster with season per-game averages.";
    const w = this.week;
    const how = this.prefs.playerWeekStats === "total" ? "totals" : "per-game averages";
    return `Current roster with week ${w.number} ${how}${w.final ? "" : " so far"}, counting every game that week (also games played for another team).`;
  }

  /** The roster's switches, note and table, redrawn together when a switch changes. */
  roster() {
    const box = el("div", { class: "roster" });
    const draw = () => box.replaceChildren(
      this.rosterControls(draw) ?? "",
      el("p", { class: "table-note" }, this.rosterNote(),
        " Stats colored best (green) to worst (red) on this team; fewest TO is best."),
      this.rosterTable());
    draw();
    return box;
  }

  historyTable() {
    const history = this.league.history(this.name);
    if (!history.length) return el("p", { class: "state" }, "No matchups yet.");
    const columns = [
      { key: "week", label: "Week", cls: "strong", dir: "asc", value: r => r.week,
        cell: r => el("a", { class: "team-link", href: "#/weekly/" + r.week }, String(r.week)) },
      { key: "opp", label: "Opponent", cls: "name", dir: "asc", value: r => r.opponent.toLowerCase(), cell: r => Widgets.team(r.opponent) },
      { key: "result", label: "Result", value: r => Widgets.RESULT_ORDER[r.result] ?? 0, cell: Widgets.result },
      { key: "score", label: "Categories", value: r => r.cat_wins - r.cat_losses, cell: Format.score },
      { key: "overall", label: "Week rank", dir: "asc", title: "Overall rank that week (1 = best)",
        value: r => r.overall_rank, cell: r => `${r.overall_rank} of ${r.of}`, tint: r => RankColor.ofRank(r.overall_rank, r.of) },
    ];
    return new SortableTable(columns, { id: "history", rows: history, defaultSort: null }).render();
  }

  render() {
    // Everything below the picker uses this team's theme color (see .team-theme in style.css).
    return [
      this.picker(),
      el("div", { class: "team-theme", style: Widgets.teamStyle(this.name) },
        Page.head(Widgets.team(this.name, { link: false }), "Season record, category ranks, roster and matchups."),
        this.summary(),
        this.rankChips(),
        this.roster(),
        el("h3", { class: "section-title" }, "Matchups"),
        this.historyTable()),
    ];
  }
}
