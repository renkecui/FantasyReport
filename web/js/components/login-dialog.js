import { League } from "../state/league.js";
import { Session } from "../state/session.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

/** "Log in": pick your team, enter the league password, optionally stay logged in. */
export class LoginDialog {
  constructor(onDone) {
    this.onDone = onDone;
  }

  open() {
    const teams = League.instance().teamNames;
    const error = el("p", { class: "form-error", role: "alert" });
    const team = el("select", { name: "team", required: true, id: "login-team" },
      el("option", { value: "" }, "Choose your team…"),
      teams.map(t => el("option", { value: t }, t)));
    const password = el("input", { type: "password", name: "password", id: "login-password", required: true,
      autocomplete: "current-password" });
    const remember = el("input", { type: "checkbox", name: "remember", id: "login-remember" });
    const submit = el("button", { type: "submit", class: "btn primary" }, "Log in");
    const dialog = el("dialog", { class: "dialog", "aria-labelledby": "login-title" });

    const form = el("form", {
      onsubmit: async e => {
        e.preventDefault();
        error.textContent = "";
        submit.disabled = true;
        submit.textContent = "Logging in…";
        try {
          await Session.instance().login(team.value, password.value, remember.checked);
          dialog.close();
          this.onDone();
        } catch (err) {
          error.textContent = err.message;
          password.select();
        } finally {
          submit.disabled = false;
          submit.textContent = "Log in";
        }
      },
    },
      el("h2", { id: "login-title" }, "Log in"),
      el("p", { class: "muted" }, "Pick your team and enter the league password."),
      el("label", { for: "login-team" }, "Team"), team,
      el("label", { for: "login-password" }, "League password"), password,
      el("label", { class: "check" }, remember, " Remember me on this device"),
      error,
      el("div", { class: "dialog-actions" },
        el("button", { type: "button", class: "btn", onclick: () => dialog.close() }, "Cancel"),
        submit));

    dialog.append(form);
    dialog.addEventListener("close", () => dialog.remove());
    document.body.append(dialog);
    dialog.showModal();
    team.focus();
  }
}
