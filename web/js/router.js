import { SeasonPage } from "./pages/season-page.js";
import { TeamPage } from "./pages/team-page.js";
import { WeeklyPage } from "./pages/weekly-page.js";
import { League } from "./state/league.js";

export class Router {
  static PAGES = { season: SeasonPage, weekly: WeeklyPage, team: TeamPage };
  static DEFAULT = "season";

  constructor(main, nav) {
    this.main = main;
    this.nav = nav;
  }

  start() {
    window.addEventListener("hashchange", () => { this.show(); window.scrollTo(0, 0); });
    this.show();
  }

  /** "#/team/Bench%20Mob" → { name: "team", param: "Bench Mob" } */
  static parse(hash) {
    const parts = hash.replace(/^#\/?/, "").split("/");
    const name = parts[0] in Router.PAGES ? parts[0] : Router.DEFAULT;
    const raw = parts.slice(1).join("/");
    try { return { name, param: decodeURIComponent(raw) }; } catch { return { name, param: raw }; }
  }

  show() {
    const { name, param } = Router.parse(location.hash);
    for (const a of this.nav.querySelectorAll("a")) {
      a.setAttribute("aria-current", a.dataset.route === name ? "page" : "false");
    }
    const page = new Router.PAGES[name](param);
    this.main.replaceChildren(...page.render().filter(Boolean));
    document.title = `${page.title} · ${League.instance().title}`;
  }
}
