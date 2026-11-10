import { SortableTable } from "../components/sortable-table.js";
import { Widgets } from "../components/widgets.js";
import { League } from "../state/league.js";
import { Preferences } from "../state/preferences.js";
import { Dom } from "../util/dom.js";
import { Format } from "../util/format.js";
import { RankColor } from "../util/rank-color.js";

const el = Dom.el;

/** Base class for a page: subclasses give a title and render() its content. */
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
   *  Cells are always tinted by rank and sort best-first on the first click.
   *  view(row) picks which { stats, ranks } to show; format(cat, value) formats a value. */
  categoryColumns(n, statsGroup, ranksGroup, { view = r => r, format = Format.category } = {}) {
    const ranks = this.prefs.mode === "ranks";
    return this.league.categories.map(cat => ({
      key: "cat:" + cat,
      label: cat,
      group: ranks ? ranksGroup : statsGroup,
      dir: "asc",
      title: `${cat}: click to sort (best first)` + (cat === "TO" ? ", fewest is best" : ""),
      value: r => view(r).ranks[cat],
      cell: r => (ranks ? String(view(r).ranks[cat]) : format(cat, view(r).stats[cat])),
      cellTitle: r => (ranks ? `${cat} ${format(cat, view(r).stats[cat])}` : `Rank ${view(r).ranks[cat]} of ${n}`),
      tint: r => RankColor.ofRank(view(r).ranks[cat], n),
    }));
  }

  /** A table with a Stats/Ranks switch that redraws it. Returns { toggle, table } holders.
   *  options may be a function, re-read on every redraw; extraControls(redraw) adds more switches. */
  switchableTable(makeColumns, options, extraControls = () => []) {
    const table = el("div");
    const toggle = el("div", { class: "controls" });
    const draw = () => {
      toggle.replaceChildren(...extraControls(draw), Widgets.modeToggle(draw));
      const opts = typeof options === "function" ? options() : options;
      table.replaceChildren(new SortableTable(makeColumns(), opts).render());
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
