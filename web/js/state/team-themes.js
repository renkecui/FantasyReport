import { ApiClient } from "./api-client.js";
import { League } from "./league.js";
import { Session } from "./session.js";
import { ThemeAssignment } from "../shared/theme-assignment.js";

/** Each team's color theme: from the Worker when it's set up, else every team's default. */
export class TeamThemes {
  static #instance = null;
  static CATALOG_URL = "themes.json";
  static FALLBACK = "#94a3b8";

  static instance() { return (TeamThemes.#instance ??= new TeamThemes()); }

  constructor() {
    if (TeamThemes.#instance) throw new Error("TeamThemes is a singleton; use TeamThemes.instance()");
    this.catalog = [];
    this.assignments = {};
  }

  async load() {
    const api = ApiClient.instance();
    if (api.enabled) {
      try {
        const res = await api.themes();
        this.catalog = res.themes;
        this.assignments = res.assignments;
        return this;
      } catch (e) {
        console.warn("Themes: using defaults,", e.message);
      }
    }
    const res = await fetch(TeamThemes.CATALOG_URL);
    this.catalog = res.ok ? await res.json() : [];
    this.assignments = ThemeAssignment.resolve(this.catalog.map(t => t.id), League.instance().teamNames);
    return this;
  }

  theme(id) { return this.catalog.find(t => t.id === id); }
  themeOf(team) { return this.theme(this.assignments[team]); }
  colorOf(team) { return this.themeOf(team)?.color ?? TeamThemes.FALLBACK; }
  takenBy(themeId, team) { return ThemeAssignment.takenBy(this.assignments, themeId, team); }

  /** Give the logged-in team this theme (rejects if another team has it). */
  async choose(themeId) {
    const session = Session.instance();
    const res = await ApiClient.instance().setTheme(session.token, themeId);
    this.assignments = res.assignments;
  }

  /** Re-read everyone's themes (e.g. after someone else took the one you wanted). */
  async refresh() {
    try {
      const res = await ApiClient.instance().themes();
      this.assignments = res.assignments;
    } catch { /* keep what we have */ }
  }
}
