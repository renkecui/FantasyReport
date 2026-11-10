export class League {
  static #instance = null;
  // Where the league data comes from. One place, so it can point elsewhere later (WEBSITE_PLAN Phase 6).
  static DATA_URL = "league.json";
  static SCHEMA_VERSION = 2;

  static instance() { return (League.#instance ??= new League()); }

  constructor() {
    if (League.#instance) throw new Error("League is a singleton; use League.instance()");
    this.data = null;
  }

  async load() {
    const res = await fetch(League.DATA_URL, { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    this.data = await res.json();
    if (this.data.schema_version !== League.SCHEMA_VERSION) {
      console.warn(`league.json schema ${this.data.schema_version}, page expects ${League.SCHEMA_VERSION}`);
    }
    return this;
  }

  get title() { return this.data.title; }
  get teamNames() { return this.data.teams.map(t => t.name); }
  get categories() { return this.data.categories; }
  get season() { return this.data.season; }
  get weeks() { return this.data.weeks; }

  /** The week in progress, or undefined when every week is final. */
  get liveWeek() { return this.weeks.find(w => !w.final); }
  get finishedWeekCount() { return this.weeks.filter(w => w.final).length; }

  /** Season totals with or without the week in progress (older league.json files only have "with"). */
  seasonRows(includeCurrentWeek) {
    return includeCurrentWeek || !this.data.season_completed ? this.data.season : this.data.season_completed;
  }

  roster(name) { return this.data.rosters[name] || []; }
  seasonRow(name) { return this.data.season.find(r => r.team === name); }

  /** Standings order: matchup wins (ties count half), then category win margin. */
  static standing(r) { return (r.wins + 0.5 * r.ties) * 10000 + (r.cat_wins - r.cat_losses); }

  place(row) { return 1 + this.season.filter(r => League.standing(r) > League.standing(row)).length; }

  /** One team's matchup in every week. */
  history(name) {
    return this.weeks.flatMap(w => {
      const r = w.rows.find(x => x.team === name);
      return r ? [{ ...r, week: w.number, of: w.rows.length }] : [];
    });
  }
}
