/** The league's team names, read from the published league.json (cached for a few minutes). */
export class LeagueTeams {
  static CACHE_MS = 5 * 60 * 1000;
  static #cache = new Map();  // url -> { names, at }

  /** fetchImpl is for tests; by default the Worker's global fetch (called unbound, as Workers require). */
  constructor(url, fetchImpl = (...args) => fetch(...args)) {
    if (!url) throw new Error("LEAGUE_JSON_URL must be set");
    this.url = url;
    this.fetchImpl = fetchImpl;
  }

  static clearCache() { LeagueTeams.#cache.clear(); }

  /** Team names in league order. */
  async names(now = Date.now()) {
    const hit = LeagueTeams.#cache.get(this.url);
    if (hit && now - hit.at < LeagueTeams.CACHE_MS) return hit.names;
    const res = await this.fetchImpl(this.url, { cf: { cacheTtl: 60 } });
    if (!res.ok) throw new Error(`league.json: HTTP ${res.status}`);
    const data = await res.json();
    const names = (data.teams || []).map(t => t.name).filter(n => typeof n === "string");
    LeagueTeams.#cache.set(this.url, { names, at: now });
    return names;
  }
}
