import { League } from "../state/league.js";
import { Session } from "../state/session.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

/**
 * The full-page login screen shown instead of the site until someone logs in.
 * Username = your team name (any capitalization), password = the league password.
 */
export class LoginGate {
  constructor(container, onDone) {
    this.container = container;
    this.onDone = onDone;
  }

  /** The league's spelling of a typed team name, or null. Case and extra spaces don't matter. */
  static matchTeam(typed, teams) {
    const key = s => s.trim().replace(/\s+/g, " ").toLowerCase();
    const want = key(typed);
    return teams.find(t => key(t) === want) ?? null;
  }

  render() {
    const teams = League.instance().teamNames;
    const error = el("p", { class: "form-error", role: "alert" });
    const username = el("input", {
      type: "text", name: "username", id: "login-username", required: true, list: "login-teams",
      autocomplete: "username", autocapitalize: "words", spellcheck: "false",
      placeholder: "Your team name", "aria-describedby": "login-username-hint",
    });
    const password = el("input", {
      type: "password", name: "password", id: "login-password", required: true,
      autocomplete: "current-password", "aria-describedby": "login-password-hint",
    });
    const remember = el("input", { type: "checkbox", name: "remember", id: "login-remember", checked: true });
    const submit = el("button", { type: "submit", class: "btn primary" }, "Log in");

    const form = el("form", {
      class: "login-card",
      onsubmit: async e => {
        e.preventDefault();
        error.textContent = "";
        const team = LoginGate.matchTeam(username.value, teams);
        if (!team) {
          error.textContent = "No team by that name. Your username is your fantasy team's name, as it appears on ESPN.";
          username.select();
          return;
        }
        submit.disabled = true;
        submit.textContent = "Logging in…";
        try {
          await Session.instance().login(team, password.value, remember.checked);
          this.onDone();
        } catch (err) {
          error.textContent = err.message;
          password.select();
          submit.disabled = false;
          submit.textContent = "Log in";
        }
      },
    },
      el("h2", { id: "login-title" }, "Log in to see the league"),
      el("p", { class: "muted" }, "This site is for league members only."),
      el("label", { for: "login-username" }, "Username"), username,
      el("p", { class: "hint", id: "login-username-hint" },
        "Hint: your username is your fantasy team name."),
      el("datalist", { id: "login-teams" }, teams.map(t => el("option", { value: t }))),
      el("label", { for: "login-password" }, "Password"), password,
      el("p", { class: "hint", id: "login-password-hint" },
        "Hint: the league password. Ask the commissioner if you don't have it."),
      el("label", { class: "check" }, remember, " Remember me on this device"),
      error,
      submit);

    this.container.replaceChildren(el("section", { class: "login-gate", "aria-labelledby": "login-title" }, form));
    document.title = `Log in · ${League.instance().title}`;
    username.focus();
  }
}
