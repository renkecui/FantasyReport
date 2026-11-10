import assert from "node:assert/strict";
import { test } from "node:test";
import { ApiWorker } from "../src/api-worker.js";
import { FakeKv } from "./fake-kv.js";
import { FakeTeams } from "./fake-teams.js";

const ORIGIN = "https://renkecui.github.io";

function worker() {
  const env = { LEAGUE_PASSWORD: "hoops", TOKEN_SECRET: "s3cret", ALLOWED_ORIGINS: ORIGIN,
    SESSION_END: "2099-01-01", LEAGUE_JSON_URL: "https://example.com/league.json", KV: new FakeKv() };
  return new ApiWorker(env, { teams: new FakeTeams(["A", "B"]) });
}

async function call(w, method, path, { body, token, origin = ORIGIN } = {}) {
  const headers = { Origin: origin };
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await w.handle(new Request(`https://api.example.com${path}`,
    { method, headers, body: body ? JSON.stringify(body) : undefined }));
  return { status: res.status, headers: res.headers, json: res.status === 204 ? null : await res.json() };
}

test("themes are public and include CORS headers for the site", async () => {
  const res = await call(worker(), "GET", "/themes");
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  assert.ok(res.json.themes.length >= 10);
  assert.notEqual(res.json.assignments.A, res.json.assignments.B);
});

test("other origins get no CORS headers; preflight works", async () => {
  const w = worker();
  assert.equal((await call(w, "GET", "/themes", { origin: "https://evil.example" })).headers.get("Access-Control-Allow-Origin"), null);
  const pre = await call(w, "OPTIONS", "/login");
  assert.equal(pre.status, 204);
  assert.match(pre.headers.get("Access-Control-Allow-Methods"), /PUT/);
});

test("log in, see who I am, pick a theme", async () => {
  const w = worker();
  const login = await call(w, "POST", "/login", { body: { team: "A", password: "hoops", remember: true } });
  assert.equal(login.status, 200);
  const me = await call(w, "GET", "/me", { token: login.json.token });
  assert.equal(me.json.team, "A");
  const before = (await call(w, "GET", "/themes")).json.assignments;
  const free = (await call(w, "GET", "/themes")).json.themes.map(t => t.id).find(id => !Object.values(before).includes(id));
  const picked = await call(w, "PUT", "/me/theme", { token: login.json.token, body: { theme: free } });
  assert.equal(picked.status, 200);
  assert.equal(picked.json.assignments.A, free);
  const taken = await call(w, "PUT", "/me/theme", { token: login.json.token, body: { theme: before.B } });
  assert.equal(taken.status, 409);
  assert.equal(taken.json.takenBy, "B");
});

test("no token or a bad token can't change themes", async () => {
  const w = worker();
  assert.equal((await call(w, "PUT", "/me/theme", { body: { theme: "royal" } })).status, 401);
  assert.equal((await call(w, "PUT", "/me/theme", { token: "a.b", body: { theme: "royal" } })).status, 401);
  assert.equal((await call(w, "POST", "/login", { body: { team: "A", password: "nope" } })).status, 401);
  assert.equal((await call(w, "GET", "/nowhere")).status, 404);
});
