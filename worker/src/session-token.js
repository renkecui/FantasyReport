/**
 * Signed session tokens: base64url(JSON payload) + "." + base64url(HMAC-SHA256 signature).
 * The key includes the league password, so changing the password logs everyone out.
 */
export class SessionToken {
  constructor(secret, leaguePassword) {
    if (!secret || !leaguePassword) throw new Error("TOKEN_SECRET and LEAGUE_PASSWORD must be set");
    this.keyText = `${secret}:${leaguePassword}`;
    this.key = null;
  }

  /** payload must include exp (seconds since 1970). */
  async sign(payload) {
    const body = SessionToken.encode(new TextEncoder().encode(JSON.stringify(payload)));
    const sig = await crypto.subtle.sign("HMAC", await this.#cryptoKey(), new TextEncoder().encode(body));
    return `${body}.${SessionToken.encode(new Uint8Array(sig))}`;
  }

  /** The payload if the signature is valid and it hasn't expired, else null. */
  async verify(token, nowSeconds = Math.floor(Date.now() / 1000)) {
    if (typeof token !== "string" || token.length > 2048) return null;
    const [body, sig, extra] = token.split(".");
    if (!body || !sig || extra !== undefined) return null;
    let ok = false;
    try {
      ok = await crypto.subtle.verify("HMAC", await this.#cryptoKey(), SessionToken.decode(sig),
        new TextEncoder().encode(body));
    } catch {
      return null;
    }
    if (!ok) return null;
    try {
      const payload = JSON.parse(new TextDecoder().decode(SessionToken.decode(body)));
      return typeof payload.exp === "number" && payload.exp > nowSeconds ? payload : null;
    } catch {
      return null;
    }
  }

  async #cryptoKey() {
    this.key ??= await crypto.subtle.importKey("raw", new TextEncoder().encode(this.keyText),
      { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
    return this.key;
  }

  static encode(bytes) {
    let s = "";
    for (const b of bytes) s += String.fromCharCode(b);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  static decode(text) {
    const b64 = text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4);
    return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  }
}
