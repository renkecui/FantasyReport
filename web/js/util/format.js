/** Formats stats and seasons for display (".482", "1,234", "2026–27"). */
export class Format {
  static PCT = new Set(["FG%", "FT%"]);

  static pct(v) { return v == null ? "–" : Number(v).toFixed(3).replace(/^0(?=\.)/, ""); }
  static int(v) { return v == null ? "–" : Math.round(v).toLocaleString(); }
  static one(v) { return v == null ? "–" : Number(v).toFixed(1); }
  static two(v) { return v == null ? "–" : Number(v).toFixed(2); }
  static category(cat, v) { return Format.PCT.has(cat) ? Format.pct(v) : Format.int(v); }
  /** A per-week average: percentages as usual, counting stats with one decimal. */
  static perWeek(cat, v) { return Format.PCT.has(cat) ? Format.pct(v) : Format.one(v); }
  static score(r) { return `${r.cat_wins}-${r.cat_losses}-${r.cat_ties}`; }
  static season(year) { return `${year - 1}–${String(year).slice(-2)}`; }
}
