import { Dom } from "../util/dom.js";
import { RankColor } from "../util/rank-color.js";

const el = Dom.el;

/**
 * columns: [{ key, label, title, group, cls, value(row), cell(row), cellTitle(row),
 *             tint(row) -> 0..1 | null, dir: "asc" | "desc" (first-click direction), sortable }]
 * options: { id, rows, defaultSort: { key, dir } | null, rowClass(row, originalIndex, isSorted),
 *            rowStyle(row) -> { cssProperty: value } }
 * Each table id remembers its sort while the page is open.
 */
export class SortableTable {
  static #sorts = new Map();

  static resetSort(id) { SortableTable.#sorts.set(id, null); }

  constructor(columns, options) {
    this.columns = columns;
    this.options = options;
    this.card = el("div", { class: "table-card" });
    if (!SortableTable.#sorts.has(options.id)) SortableTable.#sorts.set(options.id, options.defaultSort || null);
  }

  get sort() { return SortableTable.#sorts.get(this.options.id); }
  set sort(value) { SortableTable.#sorts.set(this.options.id, value); }

  render() {
    this.#draw();
    return this.card;
  }

  #sortedRows() {
    const rows = this.options.rows.map((r, i) => [r, i]);
    const s = this.sort;
    const col = s && this.columns.find(c => c.key === s.key);
    if (!col) return rows;
    const sign = s.dir === "asc" ? 1 : -1;
    return rows.sort(([a, ia], [b, ib]) => {
      const va = col.value(a), vb = col.value(b);
      if (va < vb) return -sign;
      if (va > vb) return sign;
      return ia - ib;
    });
  }

  #onSort(col) {
    const s = this.sort;
    this.sort = s && s.key === col.key
      ? { key: col.key, dir: s.dir === "asc" ? "desc" : "asc" }
      : { key: col.key, dir: col.dir || "desc" };
    this.#draw();
    const btn = this.card.querySelector(`button[data-key="${CSS.escape(col.key)}"]`);
    if (btn) btn.focus();
  }

  /** Columns grouped under shared labels, and which column indexes start a new group. */
  #groups() {
    const starts = new Set();
    const spans = [];
    this.columns.forEach((c, i) => {
      const label = c.group || "";
      const last = spans[spans.length - 1];
      if (last && last.label === label) last.span++;
      else {
        spans.push({ label, span: 1 });
        if (i > 0) starts.add(i);
      }
    });
    return { starts, spans };
  }

  #draw() {
    const s = this.sort;
    const { starts, spans } = this.#groups();
    const classes = (...names) => names.filter(Boolean).join(" ") || null;

    const head = el("thead", {},
      spans.some(g => g.label) ? el("tr", { class: "groups" },
        spans.map(g => el("th", { colspan: g.span, scope: "colgroup" }, g.label))) : null,
      el("tr", { class: "cols" }, this.columns.map((c, i) => {
        const sorted = s && s.key === c.key;
        return el("th", {
          scope: "col", class: classes(c.cls, starts.has(i) && "group-start"), title: c.title || null,
          "aria-sort": sorted ? (s.dir === "asc" ? "ascending" : "descending") : null,
        }, c.sortable === false ? c.label
          : el("button", { class: "sort", type: "button", "data-key": c.key, onclick: () => this.#onSort(c) }, c.label));
      })));

    const body = el("tbody", {}, this.#sortedRows().map(([r, i]) => el("tr", {
      class: this.options.rowClass ? this.options.rowClass(r, i, !!s) : null,
      style: this.options.rowStyle ? this.options.rowStyle(r) : null,
    }, this.columns.map((c, ci) => {
      const t = c.tint ? c.tint(r) : null;
      return el("td", {
        class: classes(c.cls, starts.has(ci) && "group-start", t != null && "tint"),
        title: c.cellTitle ? c.cellTitle(r) : null,
        style: t != null ? { "--h": RankColor.hue(t) } : null,
      }, c.cell ? c.cell(r) : c.value(r));
    }))));

    this.card.replaceChildren(el("table", {}, head, body));
  }
}
