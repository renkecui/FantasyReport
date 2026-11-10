import assert from "node:assert/strict";
import { test } from "node:test";
import { LeagueTeams } from "../src/league-teams.js";

test("reads team names from league.json and caches them", async () => {
  LeagueTeams.clearCache();
  let calls = 0;
  const fake = async () => { calls++; return new Response(JSON.stringify({ teams: [{ name: "A" }, { name: "B" }] })); };
  const teams = new LeagueTeams("https://x/league.json", fake);
  assert.deepEqual(await teams.names(1000), ["A", "B"]);
  assert.deepEqual(await teams.names(2000), ["A", "B"]);
  assert.equal(calls, 1);
  assert.deepEqual(await teams.names(1000 + LeagueTeams.CACHE_MS + 1), ["A", "B"]);
  assert.equal(calls, 2);
});

test("the default fetch is called unbound (Workers reject fetch with another `this`)", async () => {
  LeagueTeams.clearCache();
  const original = globalThis.fetch;
  globalThis.fetch = function (url) {
    if (this !== undefined && this !== globalThis) throw new TypeError("Illegal invocation");
    return Promise.resolve(new Response(JSON.stringify({ teams: [{ name: url.endsWith("x.json") ? "X" : "?" }] })));
  };
  try {
    assert.deepEqual(await new LeagueTeams("https://y/x.json").names(), ["X"]);
  } finally {
    globalThis.fetch = original;
  }
});
