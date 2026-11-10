import { Widgets } from "../components/widgets.js";
import { Page } from "./page.js";
import { League } from "../state/league.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

/** #/season: every team's season record and category totals, with ranks. */
export class SeasonPage extends Page {
  get title() { return "Season Totals"; }

  /** The week in progress, if the viewer can choose to leave it out. */
  get toggleableWeek() {
    const live = this.league.liveWeek;
    return live && this.league.data.season_completed && this.league.finishedWeekCount > 0 ? live : null;
  }

  get includeCurrentWeek() {
    return !this.toggleableWeek || this.prefs.currentWeek !== "exclude";
  }

  /** The season rows in draft order, which the Team header goes back to. */
  rows() {
    const order = this.league.draftOrder;
    return [...this.league.seasonRows(this.includeCurrentWeek)]
      .sort((a, b) => order.indexOf(a.team) - order.indexOf(b.team));
  }

  /** Per-week averages need a league.json that has them; otherwise totals are shown. */
  get perWeek() {
    return this.prefs.seasonStats === "perWeek" && this.rows().every(r => r.per_week);
  }

  /** The stats, ranks and average rank to show for a row, totals or per week. */
  view(r) { return this.perWeek ? r.per_week : r; }

  columns() {
    const rows = this.rows();
    const n = rows.length;
    const view = r => this.view(r);
    const avgs = rows.map(r => view(r).avg_rank);
    const perWeek = this.perWeek;
    return [
      { key: "team", label: "Team", cls: "name", resetsSort: true, title: "Draft order", cell: r => Widgets.team(r.team) },
      { key: "record", label: "Record", group: "Record", cls: "strong", title: "Matchup W-L-T (finished weeks)",
        value: League.standing, cell: r => r.record },
      { key: "cw", label: "Cat W", group: "Record", value: r => r.cat_wins },
      { key: "cl", label: "Cat L", group: "Record", dir: "asc", value: r => r.cat_losses },
      { key: "ct", label: "Cat T", group: "Record", value: r => r.cat_ties },
      ...(perWeek ? [{ key: "weeks", label: "Weeks", group: "Record", title: "Weeks played (byes don't count)",
        value: r => r.weeks }] : []),
      ...this.categoryColumns(n, perWeek ? "Per-week averages" : "Season totals",
        perWeek ? "League rank, per week (1 = best)" : "League rank (1 = best)",
        { view, format: perWeek ? Format.perWeek : Format.category }),
      { key: "avg", label: "Avg rank", group: "Overall", dir: "asc", title: "Average of the 9 league ranks",
        value: r => view(r).avg_rank, cell: r => Format.two(view(r).avg_rank),
        tint: r => RankColor.within(view(r).avg_rank, avgs, true) },
    ];
  }

  subtitle() {
    const total = this.league.weeks.length;
    const pct = this.perWeek
      ? "Stats are averaged per week played; FG% and FT% are the average of weekly percentages."
      : "Stats are summed; FG% and FT% are the average of weekly percentages.";
    if (!this.toggleableWeek) {
      return `Weeks 1–${total}. Record counts finished weeks; stats include any week in progress. ${pct}`;
    }
    const live = this.toggleableWeek.number;
    if (this.includeCurrentWeek) {
      return `Weeks 1–${total}, including week ${live} in progress. Record counts finished weeks only. ${pct}`;
    }
    return `Weeks 1–${this.league.finishedWeekCount}: finished weeks only, week ${live} left out. ${pct}`;
  }

  render() {
    const subtitle = document.createElement("p");
    const { toggle, table } = this.switchableTable(
      () => this.columns(),
      () => {
        subtitle.textContent = this.subtitle();
        return { id: "season", rows: this.rows(), defaultSort: { key: "record", dir: "desc" }, rowClass: Widgets.mineRow,
          rowStyle: Widgets.teamRow };
      },
      redraw => [
        Widgets.seasonStatsToggle(redraw),
        ...(this.toggleableWeek ? [Widgets.currentWeekToggle(this.toggleableWeek.number, redraw)] : []),
      ]);
    const head = Page.head("Season Totals", null, toggle);
    head.firstChild.append(subtitle);
    return [head, table];
  }
}
