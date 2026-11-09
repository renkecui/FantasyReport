import { League } from "../state/league.js";
import { Preferences } from "../state/preferences.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

export class Widgets {
  static TIEBREAK_NOTE = "Category tie; the league tiebreaker decided this result.";
  static RESULT_ORDER = { W: 3, T: 2, Live: 1, L: 0 };

  static teamHref(name) { return "#/team/" + encodeURIComponent(name); }

  static dot(name) {
    return el("span", { class: "dot", style: { background: League.instance().teamColor(name) }, "aria-hidden": "true" });
  }

  static team(name, { link = true } = {}) {
    const label = el("span", {}, name);
    return el("span", { class: "team-cell" }, Widgets.dot(name),
      link ? el("a", { class: "team-link", href: Widgets.teamHref(name) }, label) : label);
  }

  static result(row) {
    return el("span", {},
      el("span", { class: "badge " + row.result }, row.result),
      row.tiebreak ? el("span", { class: "tb", title: Widgets.TIEBREAK_NOTE }, "*") : null);
  }

  /** The Stats / Ranks switch. */
  static modeToggle(onChange) {
    const prefs = Preferences.instance();
    const button = (mode, label) => el("button", {
      type: "button", "aria-pressed": String(prefs.mode === mode),
      onclick: () => { prefs.setMode(mode); onChange(); },
    }, label);
    return el("div", { class: "segmented", role: "group", "aria-label": "Show category values or ranks" },
      button("stats", "Stats"), button("ranks", "Ranks"));
  }

  static mineRow(r) { return League.instance().isMine(r.team) ? "mine" : null; }
}
