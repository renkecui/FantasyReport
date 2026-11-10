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

  /** Roster: every stat but MIN tinted best→worst within the team (TO: fewest is best). */
  rosterTable() {
    const players = this.players;
    if (!players.length) return el("p", { class: "state" }, "No roster data.");
    const stat = (key, group, { pct = false, tint = true, lowerBetter = false } = {}) => ({
      key, label: key, group, dir: lowerBetter ? "asc" : "desc",
      value: p => p.stats[key],
      cell: p => (pct ? Format.pct(p.stats[key]) : Format.one(p.stats[key])),
      tint: tint ? p => RankColor.within(p.stats[key], players.map(x => x.stats[key]), lowerBetter) : null,
    });
    const slotGroup = s => (s === "IR" ? 2 : s === "Bench" ? 1 : 0);
    const columns = [
      { key: "slot", label: "Slot", cls: "slot", resetsSort: true, title: "Back to slot order",
        cell: p => p.slot },
      { key: "name", label: "Player", cls: "name", group: "Player", sortable: false,
        cell: p => el("span", {}, p.name, p.status ? el("span", { class: "badge status" }, p.status) : null) },
      { key: "nba", label: "Team", cls: "nba-team", group: "Player", sortable: false, value: p => p.nba_team },
      { key: "pos", label: "Pos", group: "Player", sortable: false, cell: p => p.positions || "–" },
      stat("MIN", "Shooting", { tint: false }), stat("FGM", "Shooting"), stat("FGA", "Shooting"),
      stat("FG%", "Shooting", { pct: true }),
      stat("FTM", "Shooting"), stat("FTA", "Shooting"),
      stat("FT%", "Shooting", { pct: true }),
      stat("3PM", "Per game"), stat("REB", "Per game"), stat("AST", "Per game"),
      stat("STL", "Per game"), stat("BLK", "Per game"),
      stat("TO", "Per game", { lowerBetter: true }), stat("PTS", "Per game"),
    ];
    const firstIR = players.findIndex(p => p.slot === "IR");
    return new SortableTable(columns, {
      id: "roster", rows: players, defaultSort: null, stickyName: true,
      pinned: p => p.slot === "IR",  // IR players stay at the bottom, whatever the sort
      rowClass: (p, i, sorted) => (sorted
        ? (i === firstIR && i > 0 ? "divider" : null)
        : (i > 0 && slotGroup(p.slot) !== slotGroup(players[i - 1].slot) ? "divider" : null)),
    }).render();
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
        Page.head(Widgets.team(this.name, { link: false }),
          "Current roster with season per-game averages. Stats colored best (green) to worst (red) on this team; fewest TO is best."),
        this.summary(),
        this.rankChips(),
        this.rosterTable(),
        el("h3", { class: "section-title" }, "Matchups"),
        this.historyTable()),
    ];
  }
}
