/*
 * The league website. One class per file (web/js/):
 *   Dom, Format, RankColor        stateless helpers (static methods)
 *   Preferences (singleton)       per-viewer settings kept in localStorage
 *   League (singleton)            the loaded league.json and lookups on it
 *   Widgets                       small shared pieces: team names, result badges, the Stats/Ranks switch
 *   SortableTable                 a table whose columns sort on click
 *   Page → SeasonPage, WeeklyPage, TeamPage
 *   Router                        #/season, #/weekly/<n>, #/team/<name> → a page
 *   App (singleton)               loads the data, draws the header, starts the router
 */
import { Router } from "./router.js";
import { League } from "./state/league.js";
import { Dom } from "./util/dom.js";
import { Format } from "./util/format.js";

const el = Dom.el;

export class App {
  static #instance = null;

  static instance() { return (App.#instance ??= new App()); }

  constructor() {
    if (App.#instance) throw new Error("App is a singleton; use App.instance()");
    this.main = document.getElementById("main");
    this.router = new Router(this.main, document.querySelector(".tabs"));
  }

  async start() {
    try {
      await League.instance().load();
    } catch (e) {
      this.main.replaceChildren(el("p", { class: "state error" },
        `Couldn't load the league data (${e.message}). Try reloading the page.`));
      document.getElementById("updated").textContent = "";
      return;
    }
    this.renderHeader();
    this.router.start();
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
