import assert from "node:assert/strict";
import { test } from "node:test";
import { SessionToken } from "../src/session-token.js";

test("a signed token verifies and returns its payload", async () => {
  const t = new SessionToken("secret", "pw");
  const token = await t.sign({ team: "Bench Mob", exp: 2000 });
  assert.deepEqual(await t.verify(token, 1000), { team: "Bench Mob", exp: 2000 });
});

test("expired, tampered or foreign tokens are rejected", async () => {
  const t = new SessionToken("secret", "pw");
  const token = await t.sign({ team: "A", exp: 2000 });
  assert.equal(await t.verify(token, 2000), null);
  const [body, sig] = token.split(".");
  const forged = SessionToken.encode(new TextEncoder().encode(JSON.stringify({ team: "B", exp: 2000 })));
  assert.equal(await t.verify(`${forged}.${sig}`, 1000), null);
  assert.equal(await t.verify(`${body}.${sig}x`, 1000), null);
  assert.equal(await t.verify("garbage", 1000), null);
  assert.equal(await t.verify(null, 1000), null);
});

test("changing the league password invalidates old tokens", async () => {
  const token = await new SessionToken("secret", "old").sign({ team: "A", exp: 2000 });
  assert.equal(await new SessionToken("secret", "new").verify(token, 1000), null);
});
