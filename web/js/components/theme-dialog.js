import { Session } from "../state/session.js";
import { TeamThemes } from "../state/team-themes.js";
import { Dom } from "../util/dom.js";

const el = Dom.el;

/** "Team theme": the logged-in team picks a color theme no other team has. */
export class ThemeDialog {
  constructor(onDone) {
    this.onDone = onDone;
  }

  async open() {
    const themes = TeamThemes.instance();
    const team = Session.instance().team;
    await themes.refresh();
    const error = el("p", { class: "form-error", role: "alert" });
    const dialog = el("dialog", { class: "dialog", "aria-labelledby": "theme-title" });
    const grid = el("div", { class: "swatches", role: "list" });

    const draw = () => {
      const mine = themes.assignments[team];
      grid.replaceChildren(...themes.catalog.map(t => {
        const owner = themes.takenBy(t.id, team);
        return el("div", { role: "listitem" }, el("button", {
          type: "button", class: "swatch", disabled: Boolean(owner),
          "aria-pressed": String(t.id === mine), style: { "--team": t.color },
          // Start on the current theme, not the first free one (which would look selected).
          autofocus: t.id === mine,
          title: owner ? `${t.name}: taken by ${owner}` : t.name,
          onclick: () => choose(t.id),
        },
          el("span", { class: "swatch-color", "aria-hidden": "true" }),
          el("span", { class: "swatch-name" }, t.name),
          el("span", { class: "swatch-note" }, t.id === mine ? "Current" : owner ?? "")));
      }));
    };

    const choose = async id => {
      error.textContent = "";
      try {
        await themes.choose(id);
        draw();
        this.onDone();
      } catch (e) {
        if (e.status === 401) {
          Session.instance().logout();
          dialog.close();
          this.onDone();
          return;
        }
        error.textContent = e.message;
        await themes.refresh();
        draw();
      }
    };

    draw();
    dialog.append(
      el("h2", { id: "theme-title" }, "Team theme"),
      el("p", { class: "muted" }, `Pick a color for ${team}. It's used everywhere your team appears. ` +
        "Themes another team has are taken."),
      grid, error,
      el("div", { class: "dialog-actions" },
        el("button", { type: "button", class: "btn primary", onclick: () => dialog.close() }, "Done")));
    dialog.addEventListener("close", () => dialog.remove());
    document.body.append(dialog);
    dialog.showModal();
  }
}
