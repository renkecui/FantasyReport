/** This viewer's display settings (e.g. table options), kept in localStorage. Singleton. */
export class Preferences {
  static #instance = null;
  static PREFIX = "nbafantasy.";

  static instance() { return (Preferences.#instance ??= new Preferences()); }

  constructor() {
    if (Preferences.#instance) throw new Error("Preferences is a singleton; use Preferences.instance()");
    this.mode = this.#load("mode", "stats");                    // "stats" | "ranks"
    this.currentWeek = this.#load("currentWeek", "include");    // "include" | "exclude"
    this.seasonStats = this.#load("seasonStats", "total");      // "total" | "perWeek"
  }

  /** Whether season stats are summed over the weeks or averaged per week. */
  setSeasonStats(choice) {
    this.seasonStats = choice;
    this.#save("seasonStats", choice);
  }

  setMode(mode) {
    this.mode = mode;
    this.#save("mode", mode);
  }

  /** Whether season totals include the week in progress. */
  setCurrentWeek(choice) {
    this.currentWeek = choice;
    this.#save("currentWeek", choice);
  }

  #load(key, fallback) {
    try { return localStorage.getItem(Preferences.PREFIX + key) || fallback; } catch { return fallback; }
  }
  #save(key, value) {
    try { localStorage.setItem(Preferences.PREFIX + key, value); } catch { /* storage unavailable */ }
  }
}
