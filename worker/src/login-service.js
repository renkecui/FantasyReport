import { HttpError } from "./http-error.js";

/** Checks a team name + the shared league password, and issues a session token. */
export class LoginService {
  static SHORT_SESSION_SECONDS = 12 * 60 * 60;        // without "Remember me"
  static FALLBACK_LONG_SECONDS = 180 * 24 * 60 * 60;  // "Remember me" when SESSION_END is unset or past

  /** deps: { password, tokens: SessionToken, teams: LeagueTeams, limiter: RateLimiter, sessionEnd } */
  constructor({ password, tokens, teams, limiter, sessionEnd }) {
    this.password = password;
    this.tokens = tokens;
    this.teams = teams;
    this.limiter = limiter;
    this.sessionEnd = sessionEnd;  // e.g. "2027-07-01": "Remember me" lasts until then
  }

  async login(body, visitor, nowSeconds = Math.floor(Date.now() / 1000)) {
    const team = typeof body.team === "string" ? body.team : "";
    const password = typeof body.password === "string" ? body.password : "";
    if (!team || !password) throw new HttpError(400, "Pick your team and enter the league password.");
    if (!(await this.limiter.attempt(visitor))) {
      throw new HttpError(429, "Too many attempts. Wait 15 minutes and try again.");
    }
    if (!(await this.teams.names()).includes(team)) throw new HttpError(400, "That team isn't in the league.");
    if (!(await LoginService.sameText(password, this.password))) {
      throw new HttpError(401, "Wrong league password.");
    }
    await this.limiter.reset(visitor);
    const exp = this.expiry(Boolean(body.remember), nowSeconds);
    return { token: await this.tokens.sign({ team, exp }), team, exp };
  }

  expiry(remember, nowSeconds) {
    if (!remember) return nowSeconds + LoginService.SHORT_SESSION_SECONDS;
    const end = Date.parse(this.sessionEnd || "") / 1000;
    return end > nowSeconds ? Math.floor(end) : nowSeconds + LoginService.FALLBACK_LONG_SECONDS;
  }

  /** Compare without leaking where the texts differ: compare their SHA-256 digests byte by byte. */
  static async sameText(a, b) {
    const digest = async s => new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)));
    const [x, y] = await Promise.all([digest(a), digest(b)]);
    let diff = 0;
    for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
    return diff === 0;
  }
}
