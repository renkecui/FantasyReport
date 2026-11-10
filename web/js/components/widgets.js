import { Dropdown } from "./dropdown.js";
import { Preferences } from "../state/preferences.js";
import { Session } from "../state/session.js";
import { TeamThemes } from "../state/team-themes.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

/** Small pieces shared by the pages: team names with their color dot, result badges, switches. */
export class Widgets {
  static TIEBREAK_NOTE = "Category tie; the league tiebreaker decided this result.";
  static RESULT_ORDER = { W: 3, T: 2, Live: 1, L: 0 };

  static teamHref(name) { return "#/team/" + encodeURIComponent(name); }

  /** CSS custom property with the team's theme color, for styles that use var(--team). */
  static teamStyle(name) { return { "--team": TeamThemes.instance().colorOf(name) }; }

  static dot(name) {
    return el("span", { class: "dot", style: Widgets.teamStyle(name), "aria-hidden": "true" });
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

  /** ‹ Week n › arrows around a week drop-down. weeks: the league's weeks; onPick(index). */
  static weekPicker(weeks, index, onPick) {
    return el("div", { class: "controls week-picker" },
      el("button", { class: "week-arrow prev", type: "button", "aria-label": "Previous week", disabled: index === 0,
        onclick: () => onPick(index - 1) }),
      new Dropdown({
        label: "Week", selected: index, onPick,
        // Only the most recent week can be live.
        items: weeks.map((w, i) => ({ value: i, label: `Week ${w.number}${!w.final && i === weeks.length - 1 ? " · Live" : ""}` })),
      }).render(),
      el("button", { class: "week-arrow next", type: "button", "aria-label": "Next week", disabled: index === weeks.length - 1,
        onclick: () => onPick(index + 1) }));
  }

  /** Teams roster: season per-game averages or one week's games. */
  static playerStatsToggle(onChange) {
    const prefs = Preferences.instance();
    return el("div", { class: "labeled-toggle" },
      el("span", { class: "toggle-label" }, "Player stats"),
      Widgets.segmented("Player stats for the season or one week", [["season", "Season"], ["week", "Weekly"]],
        prefs.playerStats, choice => { prefs.setPlayerStats(choice); onChange(); }));
  }

  /** A week's player stats as per-game averages or totals. */
  static playerWeekStatsToggle(onChange) {
    const prefs = Preferences.instance();
    return Widgets.segmented("Week's player stats per game or summed", [["perGame", "Per game"], ["total", "Total"]],
      prefs.playerWeekStats, choice => { prefs.setPlayerWeekStats(choice); onChange(); });
  }

  static mineRow(r) { return Session.instance().isMine(r.team) ? "mine" : null; }
  static teamRow(r) { return Widgets.teamStyle(r.team); }
}
