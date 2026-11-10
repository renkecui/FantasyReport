import { Dropdown } from "../components/dropdown.js";
import { LineChart } from "../components/line-chart.js";
import { Page } from "./page.js";
import { League } from "../state/league.js";
import { Session } from "../state/session.js";
import { TeamThemes } from "../state/team-themes.js";
import { Dom } from "../util/dom.js";
import { Format } from "../util/format.js";

const el = Dom.el;

/** #/charts: how the season has gone week by week, finished weeks only. */
export class ChartsPage extends Page {
  // Remembered while the page is open in this tab.
  static OVERALL = "Overall";
  static stat = ChartsPage.OVERALL;

  get title() { return "Charts"; }

  /** Weeks that are over: a week in progress would show half a week's stats. */
  get weeks() { return this.league.weeks.filter(w => w.final); }

  series(valueOf) {
    const themes = TeamThemes.instance(), session = Session.instance();
    return this.league.draftOrder.map(name => ({
      name, color: themes.colorOf(name), mine: session.isMine(name),
      values: this.weeks.map((w, i) => valueOf(name, w, i)),
    }));
  }

  /** Each team's place in the standings after every finished week (same order as Season Totals). */
  standings() {
    const totals = Object.fromEntries(this.league.teamNames.map(t =>
      [t, { wins: 0, losses: 0, ties: 0, cat_wins: 0, cat_losses: 0 }]));
    return this.weeks.map(w => {
      for (const r of w.rows) {
        const t = totals[r.team];
        if (!t) continue;
        t.wins += r.result === "W";
        t.losses += r.result === "L";
        t.ties += r.result === "T";
        t.cat_wins += r.cat_wins;
        t.cat_losses += r.cat_losses;
      }
      const all = Object.values(totals).map(League.standing);
      return Object.fromEntries(Object.entries(totals).map(([team, t]) => [team, {
        place: 1 + all.filter(s => s > League.standing(t)).length,
        record: `${t.wins}-${t.losses}-${t.ties}`,
      }]));
    });
  }

  rankChart() {
    const table = this.standings(), n = this.league.teamNames.length;
    const chart = new LineChart({
      label: "League standings after each week (1 = first place)",
      xLabels: this.weeks.map(w => `Wk ${w.number}`),
      series: this.series((name, w, i) => table[i][name]?.place ?? null),
      y: { min: 1, max: n, invert: true, ticks: Array.from({ length: n }, (_, i) => i + 1), title: "Place" },
      format: v => Format.ordinal(v),
      better: (a, b) => a - b,
      detail: (s, i) => table[i][s.name].record,
    });
    return el("section", { class: "chart-section" },
      el("h3", { class: "section-title" }, "Standings"),
      el("p", { class: "table-note" }, "Place after each week, by matchup record, then category wins minus losses."),
      chart.render());
  }

  /** Every team, week by week: its overall rank (the default) or its value in one stat. */
  statChart() {
    const cats = this.league.categories, n = this.league.teamNames.length;
    if (ChartsPage.stat !== ChartsPage.OVERALL && !cats.includes(ChartsPage.stat)) ChartsPage.stat = ChartsPage.OVERALL;
    const holder = el("div");
    const note = el("p", { class: "table-note" });
    const controls = el("div", { class: "controls chart-controls" });
    const draw = () => {
      const cat = ChartsPage.stat, overall = cat === ChartsPage.OVERALL;
      const row = (name, w) => w.rows.find(r => r.team === name);
      const series = this.series((name, w) => (overall ? row(name, w)?.overall_rank : row(name, w)?.stats[cat]) ?? null);
      controls.replaceChildren(new Dropdown({
        label: "Stat", selected: cat, onPick: c => { ChartsPage.stat = c; draw(); },
        items: [ChartsPage.OVERALL, ...cats].map(c => ({ value: c, label: c })),
      }).render());
      const xLabels = this.weeks.map(w => `Wk ${w.number}`);
      let chart;
      if (overall) {
        note.textContent = `Overall rank each week: teams ordered by their average rank across the ${cats.length} categories (1 = best).`;
        chart = new LineChart({
          label: note.textContent, xLabels, series,
          y: { min: 1, max: n, invert: true, ticks: Array.from({ length: n }, (_, i) => i + 1), title: "Rank" },
          format: v => Format.ordinal(v), better: (a, b) => a - b,
          detail: (s, i) => `avg rank ${Format.two(row(s.name, this.weeks[i])?.avg_rank)}`,
        });
      } else {
        const lower = (this.league.data.lower_is_better || []).includes(cat);
        const pct = Format.PCT.has(cat);
        note.textContent = `${cat} in each week.` + (lower ? " Fewer is better." : "");
        const values = series.flatMap(s => s.values).filter(v => v != null);
        const y = ChartsPage.axis(Math.min(...values), Math.max(...values), pct);
        chart = new LineChart({
          label: note.textContent, xLabels, series,
          y: { ...y, format: pct ? Format.pct : Format.int }, format: pct ? Format.pct : Format.int,
          better: lower ? (a, b) => a - b : (a, b) => b - a,
        });
      }
      holder.replaceChildren(chart.render());
    };
    draw();
    return el("section", { class: "chart-section" },
      el("div", { class: "chart-section-head" }, el("h3", { class: "section-title" }, "Stats"), controls),
      note, holder);
  }

  /** A y axis with about six round ticks around lo..hi. */
  static axis(lo, hi, pct) {
    if (lo === hi) { lo -= pct ? 0.01 : 1; hi += pct ? 0.01 : 1; }
    const raw = (hi - lo) / 5;
    const mag = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map(f => f * mag).find(s => s >= raw);
    const min = Math.floor(lo / step) * step, max = Math.ceil(hi / step) * step;
    const ticks = [];
    for (let t = min; t <= max + step / 2; t += step) ticks.push(Number(t.toFixed(6)));
    return { min, max, ticks };
  }

  render() {
    const head = Page.head("Charts", "Season trends, finished weeks only.");
    if (!this.weeks.length) return [head, el("p", { class: "state" }, "Charts start once week 1 is over.")];
    return [head, this.rankChart(), this.statChart()];
  }
}
