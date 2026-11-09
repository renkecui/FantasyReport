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

  /** A row of buttons where one is pressed. choices: [[value, label], ...] */
  static segmented(ariaLabel, choices, current, onPick) {
    return el("div", { class: "segmented", role: "group", "aria-label": ariaLabel },
      choices.map(([value, label]) => el("button", {
        type: "button", "aria-pressed": String(current === value), onclick: () => onPick(value),
      }, label)));
  }

  /** The Stats / Ranks switch. */
  static modeToggle(onChange) {
    const prefs = Preferences.instance();
    return Widgets.segmented("Show category values or ranks", [["stats", "Stats"], ["ranks", "Ranks"]],
      prefs.mode, mode => { prefs.setMode(mode); onChange(); });
  }

  /** Season stats summed over the weeks or averaged per week. */
  static seasonStatsToggle(onChange) {
    const prefs = Preferences.instance();
    return el("div", { class: "labeled-toggle" },
      el("span", { class: "toggle-label" }, "Season stats"),
      Widgets.segmented("Season stats summed or averaged per week", [["total", "Total"], ["perWeek", "Per week"]],
        prefs.seasonStats, choice => { prefs.setSeasonStats(choice); onChange(); }));
  }

  /** Include or exclude the week in progress from season totals. */
  static currentWeekToggle(weekNumber, onChange) {
    const prefs = Preferences.instance();
    return el("div", { class: "labeled-toggle" },
      el("span", { class: "toggle-label" }, `Week ${weekNumber} (live)`),
      Widgets.segmented(`Week ${weekNumber}, the week in progress`, [["include", "Include"], ["exclude", "Exclude"]],
        prefs.currentWeek, choice => { prefs.setCurrentWeek(choice); onChange(); }));
  }

  static mineRow(r) { return League.instance().isMine(r.team) ? "mine" : null; }
}
