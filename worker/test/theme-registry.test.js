import assert from "node:assert/strict";
import { test } from "node:test";
import { ThemeRegistry } from "../src/theme-registry.js";
import { FakeKv, FakeTeams } from "./fake-kv.js";

const catalog = [{ id: "red" }, { id: "blue" }, { id: "green" }];

test("teams start with different defaults", async () => {
  const reg = new ThemeRegistry(new FakeKv(), catalog, new FakeTeams(["A", "B"]));
  assert.deepEqual(await reg.assignments(), { A: "red", B: "blue" });
});

test("a team can pick a free theme, and it is saved", async () => {
  const kv = new FakeKv();
  const reg = new ThemeRegistry(kv, catalog, new FakeTeams(["A", "B"]));
  assert.deepEqual(await reg.pick("A", "green"), { A: "green", B: "blue" });
  assert.deepEqual(await new ThemeRegistry(kv, catalog, new FakeTeams(["A", "B"])).assignments(), { A: "green", B: "blue" });
});

test("a theme another team has can't be picked; unknown themes are refused", async () => {
  const reg = new ThemeRegistry(new FakeKv(), catalog, new FakeTeams(["A", "B"]));
  await assert.rejects(reg.pick("A", "blue"), e => e.status === 409 && e.extra.takenBy === "B");
  await assert.rejects(reg.pick("A", "pink"), e => e.status === 400);
});

test("re-picking your own theme is fine", async () => {
  const reg = new ThemeRegistry(new FakeKv(), catalog, new FakeTeams(["A", "B"]));
  assert.deepEqual(await reg.pick("B", "blue"), { A: "red", B: "blue" });
});
