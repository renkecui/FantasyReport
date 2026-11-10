/**
 * Talks to the Cloudflare Worker (worker/). Its address is the
 * <meta name="nbafantasy-api"> tag in index.html; when that is empty, login and theme
 * picking are hidden and every team keeps its default theme.
 */
export class ApiClient {
  static #instance = null;
  static META = "nbafantasy-api";

  static instance() { return (ApiClient.#instance ??= new ApiClient()); }

  constructor() {
    if (ApiClient.#instance) throw new Error("ApiClient is a singleton; use ApiClient.instance()");
    const meta = document.querySelector(`meta[name="${ApiClient.META}"]`);
    this.base = (meta?.content || "").trim().replace(/\/+$/, "");
  }

  get enabled() { return Boolean(this.base); }

  themes() { return this.#call("GET", "/themes"); }
  login(team, password, remember) { return this.#call("POST", "/login", { body: { team, password, remember } }); }
  me(token) { return this.#call("GET", "/me", { token }); }
  setTheme(token, theme) { return this.#call("PUT", "/me/theme", { token, body: { theme } }); }

  /** Resolves with the JSON body; rejects with an Error carrying .status and the server's message. */
  async #call(method, path, { body, token } = {}) {
    if (!this.enabled) throw Object.assign(new Error("Login isn't set up for this site."), { status: 0 });
    const headers = {};
    if (body) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    let res;
    try {
      res = await fetch(this.base + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    } catch {
      throw Object.assign(new Error("Couldn't reach the server. Check your connection and try again."), { status: 0 });
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || `HTTP ${res.status}`), { status: res.status, data });
    return data;
  }
}
