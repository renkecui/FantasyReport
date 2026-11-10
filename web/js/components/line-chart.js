import { Dom } from "../util/dom.js";

const el = Dom.el;
const SVG = "http://www.w3.org/2000/svg";

/** An SVG element: svg("line", { x1: 0, ... }, ...children) */
function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "style") for (const [p, val] of Object.entries(v)) node.style.setProperty(p, val);
    else node.setAttribute(k, v);
  }
  for (const c of children.flat(Infinity)) if (c != null) node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return node;
}

/**
 * A line chart with one line per team, styled like a win-probability chart: dashed gridlines,
 * values on the right, no point markers, and a gray crosshair (mouse, touch or arrow keys) whose
 * readout sits under the chart. Also a legend and a table view. It redraws itself to fit its width.
 *
 * new LineChart({
 *   label,                      what the chart shows (for screen readers and the table caption)
 *   xLabels: ["Wk 1", ...],     one per point
 *   series: [{ name, color, values: [number | null], mine }],
 *   y: { min, max, ticks: [..], invert, title, format },   invert: smaller values drawn higher; format: tick text
 *   format: v => text,          a value as shown in the readout and table
 *   better: (a, b) => number,   readout order, best first
 *   detail: (series, i) => text extra readout text for one team at one point
 * }).render()
 */
export class LineChart {
  static HEIGHT = 320;
  static MOBILE = 560;  // narrower than this: a shorter chart

  constructor(options) {
    Object.assign(this, { detail: () => "", better: (a, b) => b - a }, options);
    this.focus = null;   // the highlighted team, from the legend
    this.index = null;   // the point under the crosshair (null: none, the readout shows the last one)
  }

  render() {
    this.plot = el("div", { class: "chart-plot" });
    this.readout = el("div", { class: "chart-readout", "aria-live": "polite" });
    this.legend = el("ul", { class: "chart-legend", "aria-label": "Teams" }, this.series.map(s =>
      el("li", {}, el("button", {
        type: "button", class: "legend-item", style: { "--team": s.color },
        "aria-pressed": "false", title: `Highlight ${s.name}`,
        onclick: () => this.#setFocus(this.focus === s.name ? null : s.name),
        onmouseenter: () => this.#preview(s.name), onmouseleave: () => this.#preview(null),
      }, el("span", { class: "line-key", "aria-hidden": "true" }), s.name))));
    // Redraw at the plot's width whenever it changes.
    new ResizeObserver(() => this.#draw()).observe(this.plot);
    return el("div", { class: "chart" }, this.legend, this.plot, this.readout, this.#table());
  }

  #draw() {
    const width = this.plot.clientWidth;
    if (!width || width === this.width) return;
    this.width = width;
    const wide = width >= LineChart.MOBILE;
    const height = wide ? LineChart.HEIGHT : 260;
    const m = { top: 30, right: 48, bottom: 30, left: 14 };
    const n = this.xLabels.length;
    const { min, max, ticks, invert } = this.y;
    const x = i => m.left + (n === 1 ? (width - m.left - m.right) / 2 : (i * (width - m.left - m.right)) / (n - 1));
    const y = v => {
      const t = (v - min) / (max - min || 1);
      return m.top + (invert ? t : 1 - t) * (height - m.top - m.bottom);
    };
    Object.assign(this, { sx: x, sy: y, m, height });

    const grid = svg("g", { class: "chart-grid" }, ticks.map(t => [
      svg("line", { x1: m.left, x2: width - m.right, y1: y(t), y2: y(t) }),
      svg("text", { x: width - m.right + 10, y: y(t), "dominant-baseline": "middle" }, (this.y.format ?? this.format)(t)),
    ]), this.xLabels.map((label, i) =>
      // The first and last week line up with the plot's edges.
      svg("text", { x: x(i), y: height - 8, "text-anchor": n > 1 && i === 0 ? "start" : n > 1 && i === n - 1 ? "end" : "middle" }, label)));
    // What the axis measures, top left (above the best end of the scale).
    const title = this.y.title ? svg("text", { class: "chart-axis-title", x: m.left, y: 12 }, this.y.title) : null;

    // The highlighted team (and the viewer's own) draw last, on top.
    const order = [...this.series].sort((a, b) => (a.mine - b.mine));
    this.lines = svg("g", {}, order.map(s => this.#line(s)));
    this.crosshair = svg("line", { class: "chart-crosshair", y1: m.top - 8, y2: height - m.bottom, visibility: "hidden" });
    const hit = svg("rect", { class: "chart-hit", x: 0, y: 0, width, height });

    this.svg = svg("svg", {
      class: "chart-svg", width, height, viewBox: `0 0 ${width} ${height}`, tabindex: "0", role: "img",
      "aria-label": `${this.label}. Use the left and right arrow keys to read each week.`,
    }, grid, title, this.crosshair, this.lines, hit);
    this.svg.addEventListener("pointermove", e => this.#hover(e));
    this.svg.addEventListener("pointerdown", e => this.#hover(e));
    this.svg.addEventListener("pointerleave", () => this.#show(null));
    this.svg.addEventListener("keydown", e => this.#key(e));
    this.svg.addEventListener("focus", () => this.#show(n - 1));
    this.svg.addEventListener("blur", () => this.#show(null));
    this.plot.replaceChildren(this.svg);
    this.#applyFocus();
    this.#show(this.index);
  }

  /** One team's line: a path through its points (gaps for weeks without a value). Its dots show only
   *  under the crosshair. */
  #line(s) {
    let d = "", pen = false;
    s.values.forEach((v, i) => {
      if (v == null) { pen = false; return; }
      d += `${pen ? "L" : "M"}${this.sx(i).toFixed(1)},${this.sy(v).toFixed(1)}`;
      pen = true;
    });
    const dots = s.values.map((v, i) => v == null ? null
      : svg("circle", { class: "chart-dot", cx: this.sx(i), cy: this.sy(v), r: 4, "data-i": i }));
    return svg("g", { class: "chart-series" + (s.mine ? " mine" : ""), "data-team": s.name, style: { "--team": s.color } },
      svg("path", { d }), dots);
  }

  #hover(e) {
    const r = this.svg.getBoundingClientRect();
    const px = e.clientX - r.left, n = this.xLabels.length;
    let best = 0;
    for (let i = 1; i < n; i++) if (Math.abs(this.sx(i) - px) < Math.abs(this.sx(best) - px)) best = i;
    this.#show(best);
  }

  #key(e) {
    const n = this.xLabels.length;
    const moves = { ArrowLeft: (this.index ?? n) - 1, ArrowRight: (this.index ?? -1) + 1, Home: 0, End: n - 1 };
    if (!(e.key in moves)) { if (e.key === "Escape") this.#show(null); return; }
    e.preventDefault();
    this.#show(Math.min(n - 1, Math.max(0, moves[e.key])));
  }

  /** Crosshair at point i, and the readout for it; with no point, the readout shows the last one. */
  #show(i) {
    this.index = i;
    const on = i != null, at = on ? i : this.xLabels.length - 1;
    this.crosshair.setAttribute("visibility", on ? "visible" : "hidden");
    this.crosshair.setAttribute("x1", this.sx(at));
    this.crosshair.setAttribute("x2", this.sx(at));
    this.svg.querySelectorAll(".chart-dot").forEach(d => d.classList.toggle("on", on && Number(d.dataset.i) === i));
    const rows = this.series.filter(s => s.values[at] != null).sort((a, b) => this.better(a.values[at], b.values[at]));
    this.readout.replaceChildren(el("div", { class: "chart-readout-title" }, this.xLabels[at]),
      el("div", { class: "chart-readout-rows" }, rows.map(s =>
        el("div", { class: "chart-readout-row" + (this.focus === s.name ? " focus" : ""), style: { "--team": s.color } },
          el("span", { class: "line-key", "aria-hidden": "true" }),
          el("strong", {}, this.format(s.values[at])),
          el("span", { class: "chart-readout-name", title: s.name }, s.name),
          this.detail(s, at) ? el("span", { class: "chart-readout-detail" }, this.detail(s, at)) : null))));
  }

  #preview(name) { this.hovered = name; this.#applyFocus(); }

  #setFocus(name) {
    this.focus = name;
    for (const b of this.legend.querySelectorAll("button")) {
      b.setAttribute("aria-pressed", String(b.textContent === name));
    }
    this.#applyFocus();
    this.#show(this.index);
  }

  /** Fade every line but the highlighted team's, and draw it on top. */
  #applyFocus() {
    const name = this.hovered ?? this.focus;
    if (!this.lines) return;
    for (const g of [...this.lines.children]) {
      const it = g.dataset.team === name;
      g.classList.toggle("faded", name != null && !it);
      if (it) this.lines.append(g);
    }
  }

  /** The same numbers as a table, for reading without the chart. */
  #table() {
    return el("details", { class: "chart-table" },
      el("summary", {}, "Show as table"),
      el("div", { class: "table-card" }, el("table", {},
        el("caption", { class: "sr-only" }, this.label),
        el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Team"),
          this.xLabels.map(l => el("th", { scope: "col" }, l)))),
        el("tbody", {}, this.series.map(s => el("tr", {},
          el("th", { scope: "row", class: "name" }, s.name),
          s.values.map(v => el("td", {}, v == null ? "–" : this.format(v)))))))));
  }
}
