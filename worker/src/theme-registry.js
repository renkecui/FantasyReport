import { ThemeAssignment } from "../../web/js/shared/theme-assignment.js";
import { HttpError } from "./http-error.js";

/** Each team's color theme. Users' picks are kept in Workers KV; everyone else gets a default. */
export class ThemeRegistry {
  static KEY = "theme-picks";

  constructor(kv, catalog, teams) {
    this.kv = kv;
    this.catalog = catalog;
    this.teams = teams;  // LeagueTeams
  }

  get themeIds() { return this.catalog.map(t => t.id); }

  async picks() {
    try { return JSON.parse((await this.kv.get(ThemeRegistry.KEY)) || "{}"); } catch { return {}; }
  }

  /** { team: themeId } for every team. */
  async assignments() {
    return ThemeAssignment.resolve(this.themeIds, await this.teams.names(), await this.picks());
  }

  /** Give `team` the theme `themeId`, unless another team already has it. Returns the new assignments. */
  async pick(team, themeId) {
    if (!this.themeIds.includes(themeId)) throw new HttpError(400, "Unknown theme.");
    const names = await this.teams.names();
    const picks = await this.picks();
    const current = ThemeAssignment.resolve(this.themeIds, names, picks);
    const owner = ThemeAssignment.takenBy(current, themeId, team);
    if (owner) throw new HttpError(409, `That theme belongs to ${owner}.`, { takenBy: owner });
    // Keep only picks for teams still in the league.
    const next = Object.fromEntries(Object.entries(picks).filter(([t]) => names.includes(t)));
    next[team] = themeId;
    await this.kv.put(ThemeRegistry.KEY, JSON.stringify(next));
    return ThemeAssignment.resolve(this.themeIds, names, next);
  }
}
