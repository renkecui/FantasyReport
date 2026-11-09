export class Preferences {
  static #instance = null;
  static PREFIX = "nbafantasy.";

  static instance() { return (Preferences.#instance ??= new Preferences()); }

  constructor() {
    if (Preferences.#instance) throw new Error("Preferences is a singleton; use Preferences.instance()");
    this.mode = this.#load("mode", "stats");  // "stats" | "ranks"
  }

  setMode(mode) {
    this.mode = mode;
    this.#save("mode", mode);
  }

  #load(key, fallback) {
    try { return localStorage.getItem(Preferences.PREFIX + key) || fallback; } catch { return fallback; }
  }
  #save(key, value) {
    try { localStorage.setItem(Preferences.PREFIX + key, value); } catch { /* storage unavailable */ }
  }
}
