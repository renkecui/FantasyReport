import { SortableTable } from "../components/sortable-table.js";
import { Widgets } from "../components/widgets.js";
import { League } from "../state/league.js";
import { Preferences } from "../state/preferences.js";
import { Dom } from "../util/dom.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

const el = Dom.el;

export class Page {
  constructor(param) {
    this.league = League.instance();
    this.prefs = Preferences.instance();
    this.param = param;
  }

  /** Document title for this page. */
  get title() { return ""; }

  /** Returns the nodes to show in <main>. */
  render() { return []; }

  /** The nine category columns. "stats" mode shows values, "ranks" mode shows ranks.
   *  Cells are always tinted by rank and sort best-first on the first click. */
  categoryColumns(n, statsGroup, ranksGroup) {
    const ranks = this.prefs.mode === "ranks";
    return this.league.categories.map(cat => ({
      key: "cat:" + cat,
      label: cat,
      group: ranks ? ranksGroup : statsGroup,
      dir: "asc",
      title: `${cat}: click to sort (best first)` + (cat === "TO" ? ", fewest is best" : ""),
      value: r => r.ranks[cat],
      cell: r => (ranks ? String(r.ranks[cat]) : Format.category(cat, r.stats[cat])),
      cellTitle: r => (ranks ? `${cat} ${Format.category(cat, r.stats[cat])}` : `Rank ${r.ranks[cat]} of ${n}`),
      tint: r => RankColor.ofRank(r.ranks[cat], n),
    }));
  }

  /** A table with a Stats/Ranks switch that redraws it. Returns { toggle, table } holders. */
  switchableTable(makeColumns, options) {
    const table = el("div");
    const toggle = el("div", { class: "controls" });
    const draw = () => {
      toggle.replaceChildren(Widgets.modeToggle(draw));
      table.replaceChildren(new SortableTable(makeColumns(), options).render());
    };
    draw();
    return { toggle, table };
  }

  static head(title, subtitle, ...controls) {
    return el("div", { class: "page-head" },
      el("div", {}, el("h2", {}, title), subtitle ? el("p", {}, subtitle) : null),
      ...controls);
  }
}
