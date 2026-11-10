import assert from "node:assert/strict";
import { test } from "node:test";
import { HttpError } from "../src/http-error.js";
import { LoginService } from "../src/login-service.js";
import { RateLimiter } from "../src/rate-limiter.js";
import { SessionToken } from "../src/session-token.js";
import { FakeKv } from "./fake-kv.js";
import { FakeTeams } from "./fake-teams.js";

function service(kv = new FakeKv()) {
  const tokens = new SessionToken("secret", "hoops");
  return {
    tokens,
    login: new LoginService({
      password: "hoops", tokens, teams: new FakeTeams(["A", "B"]),
      limiter: new RateLimiter(kv, { limit: 3 }), sessionEnd: "2027-07-01",
    }),
  };
}
const NOW = Date.parse("2026-11-09T12:00:00Z") / 1000;

test("right team and password gives a token for that team", async () => {
  const { login, tokens } = service();
  const res = await login.login({ team: "A", password: "hoops" }, "1.2.3.4", NOW);
  assert.equal(res.team, "A");
  assert.equal(res.exp, NOW + LoginService.SHORT_SESSION_SECONDS);
  assert.equal((await tokens.verify(res.token, NOW)).team, "A");
});

test("remember me lasts until the end of the season", async () => {
  const { login } = service();
  const res = await login.login({ team: "B", password: "hoops", remember: true }, "ip", NOW);
  assert.equal(res.exp, Date.parse("2027-07-01") / 1000);
});

test("wrong password, unknown team and missing fields are refused", async () => {
  const { login } = service();
  await assert.rejects(login.login({ team: "A", password: "nope" }, "ip", NOW), e => e instanceof HttpError && e.status === 401);
  await assert.rejects(login.login({ team: "Z", password: "hoops" }, "ip", NOW), e => e.status === 400);
  await assert.rejects(login.login({ team: "A" }, "ip", NOW), e => e.status === 400);
});

test("too many attempts are blocked, and a good login clears the count", async () => {
  const kv = new FakeKv();
  const { login } = service(kv);
  for (let i = 0; i < 3; i++) {
    await assert.rejects(login.login({ team: "A", password: "x" }, "ip", NOW), e => e.status === 401);
  }
  await assert.rejects(login.login({ team: "A", password: "hoops" }, "ip", NOW), e => e.status === 429);
  const other = await login.login({ team: "A", password: "hoops" }, "other-ip", NOW);
  assert.equal(other.team, "A");
  assert.equal(await kv.get("rate:other-ip"), null);
});
