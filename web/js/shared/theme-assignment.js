/**
 * Which color theme each team has. Shared by the website and the Cloudflare Worker, so both
 * always agree. A team keeps the theme it picked; every other team gets a default, and no two
 * teams ever share a theme.
 */
export class ThemeAssignment {
  /**
   * themeIds: every theme id, in catalog order. teams: team names, in league order.
   * picks: { team: themeId } chosen by logged-in users.
   * Returns { team: themeId }: valid picks first; then each remaining team gets its own default
   * (the theme at its league position) if that's free; then any team still without one gets the
   * next unused theme. Defaults differ for every team and don't shift when someone else picks.
   */
  static resolve(themeIds, teams, picks = {}) {
    const out = {};
    const used = new Set();
    for (const team of teams) {
      const pick = picks[team];
      if (pick && themeIds.includes(pick) && !used.has(pick)) {
        out[team] = pick;
        used.add(pick);
      }
    }
    teams.forEach((team, i) => {
      const own = themeIds[i % themeIds.length];
      if (!out[team] && own && !used.has(own)) {
        out[team] = own;
        used.add(own);
      }
    });
    teams.forEach((team, i) => {
      if (out[team]) return;
      for (let k = 0; k < themeIds.length; k++) {
        const id = themeIds[(i + k) % themeIds.length];
        if (!used.has(id)) {
          out[team] = id;
          used.add(id);
          return;
        }
      }
    });
    return out;
  }

  /** The team (other than `team`) that already has `themeId`, or null. */
  static takenBy(assignments, themeId, team) {
    const owner = Object.keys(assignments).find(t => assignments[t] === themeId && t !== team);
    return owner ?? null;
  }
}
