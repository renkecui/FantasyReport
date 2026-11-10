/** The league data (league.json) and lookups on it. Singleton: use League.instance(). */
export class League {
  static #instance = null;
  // Where the league data comes from (published next to the page by the daily run).
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
  /** Team names in draft order (first-round picks); ESPN order before the draft or in older files. */
  get draftOrder() {
    const order = this.data.draft_order || [];
    return order.length === this.teamNames.length ? order : this.teamNames;
  }
  get categories() { return this.data.categories; }
  get season() { return this.data.season; }
  /** Weeks up to the current one: a week after the one in progress isn't shown. */
  get weeks() {
    const all = this.data.weeks;
    const live = all.findIndex(w => !w.final);
    return live === -1 ? all : all.slice(0, live + 1);
  }

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
