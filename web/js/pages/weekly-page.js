import { Widgets } from "../components/widgets.js";
import { Page } from "./page.js";
import { Dom } from "../util/dom.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

const el = Dom.el;

export class WeeklyPage extends Page {
  get title() { return "Weekly Stats"; }

  constructor(param) {
    super(param);
    const weeks = this.league.weeks;
    this.week = weeks.find(w => String(w.number) === String(param)) || weeks[weeks.length - 1];
    this.index = weeks.indexOf(this.week);
  }

  static go(week) { if (week) location.hash = "#/weekly/" + week.number; }

  picker() {
    const weeks = this.league.weeks, idx = this.index;
    return el("div", { class: "controls" },
      el("button", { class: "btn", type: "button", "aria-label": "Previous week", disabled: idx === 0,
        onclick: () => WeeklyPage.go(weeks[idx - 1]) }, "‹"),
      el("select", { "aria-label": "Week", onchange: e => WeeklyPage.go(weeks[Number(e.target.value)]) },
        weeks.map((w, i) => el("option", { value: i, selected: i === idx }, `Week ${w.number}${w.final ? "" : " · Live"}`))),
      el("button", { class: "btn", type: "button", "aria-label": "Next week", disabled: idx === weeks.length - 1,
        onclick: () => WeeklyPage.go(weeks[idx + 1]) }, "›"));
  }

  /** One card per matchup; rows come in pairs (team, opponent). */
  matchupCards() {
    const rows = this.week.rows;
    const seen = new Set();
    const side = x => el("div", { class: "matchup-side" + (x.result === "W" ? " winner" : "") },
      Widgets.team(x.team), el("span", { class: "score" }, Format.score(x), Widgets.result(x)));
    const cards = [];
    for (const r of rows) {
      if (seen.has(r.team)) continue;
      const o = rows.find(x => x.team === r.opponent && x.opponent === r.team);
      seen.add(r.team);
      if (o) seen.add(o.team);
      const mine = this.league.isMine(r.team) || (o && this.league.isMine(o.team));
      cards.push(el("div", { class: "matchup" + (mine ? " mine" : "") }, side(r), o ? side(o) : null));
    }
    return el("div", { class: "matchups" }, cards);
  }

  columns() {
    const n = this.week.rows.length;
    return [
      { key: "team", label: "Team", cls: "name", dir: "asc", value: r => r.team.toLowerCase(), cell: r => Widgets.team(r.team) },
      { key: "opp", label: "Opponent", cls: "name", group: "Matchup", dir: "asc", value: r => r.opponent.toLowerCase(),
        cell: r => Widgets.team(r.opponent) },
      { key: "result", label: "Result", group: "Matchup", value: r => Widgets.RESULT_ORDER[r.result] ?? 0, cell: Widgets.result },
      { key: "cw", label: "Cat W", group: "Matchup", value: r => r.cat_wins },
      { key: "cl", label: "Cat L", group: "Matchup", dir: "asc", value: r => r.cat_losses },
      { key: "ct", label: "Cat T", group: "Matchup", value: r => r.cat_ties },
      { key: "avg", label: "Avg rank", group: "Overall", dir: "asc", title: "Average of the 9 category ranks this week",
        value: r => r.avg_rank, cell: r => Format.two(r.avg_rank) },
      { key: "overall", label: "Overall", group: "Overall", dir: "asc", cls: "strong",
        title: "Week rank by average category rank (1 = best)", value: r => r.overall_rank,
        tint: r => RankColor.ofRank(r.overall_rank, n) },
      ...this.categoryColumns(n, "Category stats", "Weekly rank (1 = best)"),
    ];
  }

  render() {
    if (!this.week) return [el("p", { class: "state" }, "No matchups yet.")];
    const wk = this.week;
    const { toggle, table } = this.switchableTable(() => this.columns(), {
      id: "weekly", rows: wk.rows, defaultSort: { key: "overall", dir: "asc" }, rowClass: Widgets.mineRow,
    });
    const status = el("span", { class: "badge " + (wk.final ? "T" : "Live") }, wk.final ? "Final" : "Live");
    return [
      Page.head([`Week ${wk.number} `, status],
        wk.final ? "Final results." : "In progress: results update as games are played.", this.picker()),
      this.matchupCards(),
      el("div", { class: "page-head", style: { "margin-top": "22px" } },
        el("div", {}, el("h3", { class: "section-title", style: { margin: 0 } }, "Category breakdown"),
          el("p", {}, "Ranks compare every team this week. Ties share the better rank.")),
        toggle),
      table,
    ];
  }
}
