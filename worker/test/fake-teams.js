/** A stand-in for LeagueTeams with a fixed list of team names. */
export class FakeTeams {
  constructor(names) { this.list = names; }
  async names() { return this.list; }
}
