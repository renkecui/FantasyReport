import catalog from "../../web/themes.json" with { type: "json" };
import { Http } from "./http.js";
import { HttpError } from "./http-error.js";
import { LeagueTeams } from "./league-teams.js";
import { LoginService } from "./login-service.js";
import { RateLimiter } from "./rate-limiter.js";
import { SessionToken } from "./session-token.js";
import { ThemeRegistry } from "./theme-registry.js";

/**
 * The website's API.
 *   GET  /themes     every theme and which team has it (public)
 *   POST /login      { team, password, remember } -> { token, team, exp }
 *   GET  /me         who the token belongs to
 *   PUT  /me/theme   { theme } -> new assignments (logged in; theme must be free)
 * env: LEAGUE_PASSWORD, TOKEN_SECRET (secrets); LEAGUE_JSON_URL, ALLOWED_ORIGINS, SESSION_END (vars);
 *      KV (Workers KV namespace).
 */
export class ApiWorker {
  constructor(env, deps = {}) {
    this.env = env;
    this.origins = String(env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
    this.teams = deps.teams ?? new LeagueTeams(env.LEAGUE_JSON_URL);
    this.themes = deps.themes ?? new ThemeRegistry(env.KV, catalog, this.teams);
    this.tokens = deps.tokens ?? new SessionToken(env.TOKEN_SECRET, env.LEAGUE_PASSWORD);
    this.login = deps.login ?? new LoginService({
      password: env.LEAGUE_PASSWORD, tokens: this.tokens, teams: this.teams,
      limiter: new RateLimiter(env.KV, { prefix: "login:" }), sessionEnd: env.SESSION_END,
    });
  }

  async handle(request) {
    const cors = Http.cors(request, this.origins);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    try {
      const res = await this.route(request);
      return Http.json(res.body, res.status ?? 200, cors);
    } catch (e) {
      if (e instanceof HttpError) return Http.json({ error: e.message, ...e.extra }, e.status, cors);
      console.error(e);
      return Http.json({ error: "Something went wrong. Try again later." }, 500, cors);
    }
  }

  async route(request) {
    const { pathname } = new URL(request.url);
    const key = `${request.method} ${pathname.replace(/\/+$/, "") || "/"}`;
    switch (key) {
      case "GET /themes":
        return { body: { themes: catalog, assignments: await this.themes.assignments() } };
      case "POST /login": {
        const body = await Http.body(request);
        if (!body) throw new HttpError(400, "Send JSON: { team, password, remember }.");
        const visitor = request.headers.get("CF-Connecting-IP") || "unknown";
        return { body: await this.login.login(body, visitor) };
      }
      case "GET /me": {
        const session = await this.session(request);
        return { body: { team: session.team, exp: session.exp } };
      }
      case "PUT /me/theme": {
        const session = await this.session(request);
        const body = await Http.body(request);
        if (!body || typeof body.theme !== "string") throw new HttpError(400, "Send JSON: { theme }.");
        return { body: { assignments: await this.themes.pick(session.team, body.theme) } };
      }
      default:
        throw new HttpError(404, "Not found.");
    }
  }

  async session(request) {
    const payload = await this.tokens.verify(Http.bearer(request));
    if (!payload) throw new HttpError(401, "Please log in again.");
    if (!(await this.teams.names()).includes(payload.team)) throw new HttpError(401, "Please log in again.");
    return payload;
  }
}
