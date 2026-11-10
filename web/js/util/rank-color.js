/** Colors ranks on a green (best) to red (worst) scale. */
export class RankColor {
  /** Hue for a position on the scale: 0 = best (green) … 1 = worst (red). */
  static hue(t) { return Math.round(140 * (1 - Math.min(1, Math.max(0, t)))); }
  /** Where a rank sits on the scale among n teams. */
  static ofRank(rank, n) { return n <= 1 ? 0 : (rank - 1) / (n - 1); }
  /** Where a value sits between the best and worst of `values`. */
  static within(value, values, lowerIsBetter) {
    const lo = Math.min(...values), hi = Math.max(...values);
    if (hi === lo) return 0;
    return lowerIsBetter ? (value - lo) / (hi - lo) : (hi - value) / (hi - lo);
  }
}
