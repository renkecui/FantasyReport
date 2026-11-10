/*
 * The league website. One class per file (web/js/):
 *   Dom, Format, RankColor        stateless helpers (static methods)
 *   ThemeAssignment               which theme each team has (shared with the Worker)
 *   Preferences (singleton)       per-viewer settings kept in localStorage
 *   League (singleton)            the loaded league.json and lookups on it
 *   ApiClient (singleton)         calls the Cloudflare Worker (login, themes)
 *   Session (singleton)           who is logged in (a session token, never the password)
 *   TeamThemes (singleton)        each team's color theme
 *   Widgets                       small shared pieces: team names, result badges, switches
 *   SortableTable                 a table whose columns sort on click
 *   LineChart, Dropdown           a team-by-week line chart; a drop-down list
 *   LoginGate                     the login screen shown instead of the site until you log in
 *   AccountMenu, ThemeDialog      the header's account menu and its theme dialog
 *   Page → SeasonPage, WeeklyPage, TeamPage, ChartsPage
 *   Router                        #/season, #/weekly/<n>, #/team/<name>, #/charts → a page
 *   App (singleton)               loads everything, draws the header, starts the router
 */
import { AccountMenu } from "./components/account-menu.js";
import { LoginGate } from "./components/login-gate.js";
import { Router } from "./router.js";
import { ApiClient } from "./state/api-client.js";
import { League } from "./state/league.js";
import { Session } from "./state/session.js";
import { TeamThemes } from "./state/team-themes.js";
import { Dom } from "./util/dom.js";
import { Format } from "./util/format.js";

const el = Dom.el;

/** Starts the site: loads the league and themes, then shows the login screen or the current page. */
export class App {
  static #instance = null;

  static instance() { return (App.#instance ??= new App()); }

  constructor() {
    if (App.#instance) throw new Error("App is a singleton; use App.instance()");
    this.main = document.getElementById("main");
    this.router = new Router(this.main, document.querySelector(".tabs"), () => this.locked);
    this.account = new AccountMenu(document.getElementById("account"), () => this.refresh());
    this.gate = new LoginGate(this.main, () => this.refresh());
  }

  /** With login set up (the Worker's address in index.html), nobody sees the site until they log in. */
  get locked() { return ApiClient.instance().enabled && !Session.instance().loggedIn; }

  async start() {
    try {
      await League.instance().load();
      await TeamThemes.instance().load();
    } catch (e) {
      this.main.replaceChildren(el("p", { class: "state error" },
        `Couldn't load the league data (${e.message}). Try reloading the page.`));
      document.getElementById("updated").textContent = "";
      return;
    }
    this.renderHeader();
    this.router.start();
    this.refresh();
    // A saved login may have been revoked (e.g. the league password changed).
    const session = Session.instance();
    if (session.loggedIn) session.check().then(() => { if (!session.loggedIn) this.refresh(); });
  }

  /** Redraw after logging in or out, or a theme change: the login screen, or the current page. */
  refresh() {
    const locked = this.locked;
    document.body.classList.toggle("locked", locked);
    this.account.render();
    if (locked) this.gate.render();
    else this.router.show();
  }

  renderHeader() {
    const league = League.instance();
    document.getElementById("league-title").textContent = league.title;
    const when = new Date(league.data.generated_at);
    const stamp = isNaN(when) ? "" : when.toLocaleString(undefined, {
      month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    });
    document.getElementById("updated").textContent =
      `${Format.season(league.data.season_year)} season · Updated ${stamp}`;
  }
}
