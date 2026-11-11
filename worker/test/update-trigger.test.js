import assert from "node:assert/strict";
import { test } from "node:test";
import { UpdateTrigger } from "../src/update-trigger.js";

const ENV = { GITHUB_TOKEN: "t0ken", GITHUB_REPO: "me/FantasyReport" };

// Like Cloudflare's fetch, it refuses to run as a method of another object ("Illegal invocation").
function fakeFetch(status = 204) {
  const calls = [];
  const fn = async function (url, init) {
    if (this !== undefined && this !== globalThis) throw new TypeError("Illegal invocation");
    calls.push({ url, init });
    return new Response(status === 204 ? null : "nope", { status });
  };
  return { fn, calls };
}

test("only the cron in the 7 AM or 3 PM New York hour is due, in winter and summer", () => {
  assert.equal(UpdateTrigger.isDue(new Date("2026-11-11T12:05:00Z")), true);   // 7:05 AM EST
  assert.equal(UpdateTrigger.isDue(new Date("2026-11-11T11:05:00Z")), false);  // 6:05 AM EST
  assert.equal(UpdateTrigger.isDue(new Date("2026-11-11T20:05:00Z")), true);   // 3:05 PM EST
  assert.equal(UpdateTrigger.isDue(new Date("2027-04-01T11:05:00Z")), true);   // 7:05 AM EDT
  assert.equal(UpdateTrigger.isDue(new Date("2027-04-01T12:05:00Z")), false);  // 8:05 AM EDT
  assert.equal(UpdateTrigger.isDue(new Date("2027-04-01T19:05:00Z")), true);   // 3:05 PM EDT
});

test("starts the workflow on main with the token", async () => {
  const { fn, calls } = fakeFetch();
  assert.equal(await new UpdateTrigger(ENV, fn).run(new Date("2026-11-11T12:05:00Z")), "started");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://api.github.com/repos/me/FantasyReport/actions/workflows/update.yml/dispatches");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers.Authorization, "Bearer t0ken");
  assert.deepEqual(JSON.parse(calls[0].init.body), { ref: "main" });
});

test("does nothing outside the update hours or without a token", async () => {
  const { fn, calls } = fakeFetch();
  assert.equal(await new UpdateTrigger(ENV, fn).run(new Date("2026-11-11T11:05:00Z")), "not due");
  assert.equal(await new UpdateTrigger({ GITHUB_REPO: "me/r" }, fn).run(new Date("2026-11-11T12:05:00Z")), "no token");
  assert.equal(calls.length, 0);
});

test("a refusal from GitHub is an error, so it shows in the Worker's logs", async () => {
  const { fn } = fakeFetch(401);
  await assert.rejects(new UpdateTrigger(ENV, fn).run(new Date("2026-11-11T12:05:00Z")), /HTTP 401/);
});
