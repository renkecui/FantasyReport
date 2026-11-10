import assert from "node:assert/strict";
import { test } from "node:test";
import { ThemeAssignment } from "../../web/js/shared/theme-assignment.js";

const ids = ["red", "blue", "green", "gold"];

test("every team gets a different default theme, by league order", () => {
  assert.deepEqual(ThemeAssignment.resolve(ids, ["A", "B", "C"]), { A: "red", B: "blue", C: "green" });
});

test("picks win, and defaults skip themes that are picked", () => {
  const out = ThemeAssignment.resolve(ids, ["A", "B", "C"], { C: "red" });
  assert.deepEqual(out, { C: "red", B: "blue", A: "green" });  // B keeps its default
  assert.equal(new Set(Object.values(out)).size, 3);
});

test("invalid or duplicate picks are ignored", () => {
  const out = ThemeAssignment.resolve(ids, ["A", "B"], { A: "nope", B: "blue", Z: "red" });
  assert.deepEqual(out, { B: "blue", A: "red" });
  const dup = ThemeAssignment.resolve(ids, ["A", "B"], { A: "gold", B: "gold" });
  assert.equal(dup.A, "gold");
  assert.notEqual(dup.B, "gold");
});

test("takenBy names the other team that has a theme", () => {
  const a = { A: "red", B: "blue" };
  assert.equal(ThemeAssignment.takenBy(a, "blue", "A"), "B");
  assert.equal(ThemeAssignment.takenBy(a, "blue", "B"), null);
  assert.equal(ThemeAssignment.takenBy(a, "gold", "A"), null);
});
