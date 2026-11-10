import { ApiClient } from "./api-client.js";

/**
 * Who is logged in. Keeps the Worker's session token (never the password): in localStorage with
 * "Remember me", otherwise in sessionStorage so it ends when the browser closes.
 */
export class Session {
  static #instance = null;
  static KEY = "nbafantasy.session";

  static instance() { return (Session.#instance ??= new Session()); }

  constructor() {
    if (Session.#instance) throw new Error("Session is a singleton; use Session.instance()");
    this.token = null;
    this.team = null;
    this.exp = 0;
    this.#restore();
  }

  get loggedIn() { return Boolean(this.token) && this.exp * 1000 > Date.now(); }
  isMine(team) { return this.loggedIn && team === this.team; }

  async login(team, password, remember) {
    const res = await ApiClient.instance().login(team, password, remember);
    this.#set(res.token, res.team, res.exp);
    this.#store(remember ? localStorage : sessionStorage, res.token);
  }

  logout() {
    this.token = null;
    this.team = null;
    this.exp = 0;
    for (const storage of Session.#storages()) {
      try { storage.removeItem(Session.KEY); } catch { /* storage unavailable */ }
    }
  }

  /** Ask the server whether the saved login still works (e.g. after a password change). */
  async check() {
    if (!this.loggedIn) return;
    try {
      await ApiClient.instance().me(this.token);
    } catch (e) {
      if (e.status === 401) this.logout();
    }
  }

  #set(token, team, exp) {
    this.token = token;
    this.team = team;
    this.exp = exp;
  }

  #store(storage, token) {
    this.logout();
    this.#set(token, ...Session.#decode(token));
    try { storage.setItem(Session.KEY, token); } catch { /* storage unavailable: logged in until reload */ }
  }

  #restore() {
    for (const storage of Session.#storages()) {
      let token = null;
      try { token = storage.getItem(Session.KEY); } catch { /* storage unavailable */ }
      if (!token) continue;
      const [team, exp] = Session.#decode(token);
      if (team && exp * 1000 > Date.now()) {
        this.#set(token, team, exp);
        return;
      }
      try { storage.removeItem(Session.KEY); } catch { /* ignore */ }
    }
  }

  static #storages() {
    const out = [];
    try { out.push(localStorage); } catch { /* unavailable */ }
    try { out.push(sessionStorage); } catch { /* unavailable */ }
    return out;
  }

  /** [team, exp] from the token's payload (the server checks the signature, not the page). */
  static #decode(token) {
    try {
      const body = token.split(".")[0].replace(/-/g, "+").replace(/_/g, "/");
      const bytes = Uint8Array.from(atob(body), c => c.charCodeAt(0));
      const payload = JSON.parse(new TextDecoder().decode(bytes));
      return [payload.team, payload.exp];
    } catch {
      return [null, 0];
    }
  }
}
