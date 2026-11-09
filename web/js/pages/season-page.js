import { Widgets } from "../components/widgets.js";
import { Page } from "./page.js";
import { League } from "../state/league.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

export class SeasonPage extends Page {
  get title() { return "Season Totals"; }

  columns() {
    const rows = this.league.season;
    const n = rows.length;
    const avgs = rows.map(r => r.avg_rank);
    return [
      { key: "team", label: "Team", cls: "name", dir: "asc", value: r => r.team.toLowerCase(), cell: r => Widgets.team(r.team) },
      { key: "record", label: "Record", group: "Record", cls: "strong", title: "Matchup W-L-T (finished weeks)",
        value: League.standing, cell: r => r.record },
      { key: "cw", label: "Cat W", group: "Record", value: r => r.cat_wins },
      { key: "cl", label: "Cat L", group: "Record", dir: "asc", value: r => r.cat_losses },
      { key: "ct", label: "Cat T", group: "Record", value: r => r.cat_ties },
      ...this.categoryColumns(n, "Season stats", "League rank (1 = best)"),
      { key: "avg", label: "Avg rank", group: "Overall", dir: "asc", title: "Average of the 9 league ranks",
        value: r => r.avg_rank, cell: r => Format.two(r.avg_rank), tint: r => RankColor.within(r.avg_rank, avgs, true) },
    ];
  }

  render() {
    const { toggle, table } = this.switchableTable(() => this.columns(), {
      id: "season", rows: this.league.season, defaultSort: { key: "record", dir: "desc" }, rowClass: Widgets.mineRow,
    });
    return [
      Page.head("Season Totals",
        `Weeks 1–${this.league.weeks.length}. Record counts finished weeks; stats include the week in progress. ` +
        "FG% and FT% are the average of weekly percentages.", toggle),
      table,
    ];
  }
}
