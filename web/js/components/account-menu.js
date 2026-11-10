import { ThemeDialog } from "./theme-dialog.js";
import { Widgets } from "./widgets.js";
import { ApiClient } from "../state/api-client.js";
import { Session } from "../state/session.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

/** The header's account area: your team with "Team theme" and "Log out" (empty when logged out). */
export class AccountMenu {
  constructor(container, onChange) {
    this.container = container;
    this.onChange = onChange;
  }

  render() {
    if (!ApiClient.instance().enabled) {
      this.container.replaceChildren();
      return;
    }
    const session = Session.instance();
    if (!session.loggedIn) {
      this.container.replaceChildren();
      return;
    }
    const menu = el("details", { class: "account-menu" },
      el("summary", { "aria-label": `Logged in as ${session.team}` }, Widgets.dot(session.team),
        el("span", { class: "account-name" }, session.team)),
      el("div", { class: "menu", role: "menu" },
        el("button", { type: "button", role: "menuitem", onclick: () => {
          menu.open = false;
          new ThemeDialog(this.onChange).open();
        } }, "Team theme…"),
        el("button", { type: "button", role: "menuitem", onclick: () => {
          menu.open = false;
          session.logout();
          this.onChange();
        } }, "Log out")));
    this.container.replaceChildren(menu);
  }
}
