import { Dom } from "../util/dom.js";

const el = Dom.el;

/**
 * A custom drop-down list (styled like NBA.com's menus): a button that opens a list of at most
 * VISIBLE items, scrolling for the rest. Works with the mouse and the keyboard (arrows, Home/End,
 * Enter/Space to pick, Escape to close).
 *
 * new Dropdown({ label: "Week", items: [{ label, value, live }], selected: value, onPick: value => ... })
 * An item with live: true gets a red "· Live" after its label.
 */
export class Dropdown {
  static VISIBLE = 5;
  static #count = 0;

  constructor({ label, items, selected, onPick }) {
    this.label = label;
    this.items = items;
    this.selected = selected;
    this.onPick = onPick;
    this.id = `dropdown-${++Dropdown.#count}`;
    this.active = Math.max(0, items.findIndex(i => i.value === selected));
  }

  /** An item's text: its label, plus a red "· Live" for the week in progress. */
  static #text(item) {
    return [item?.label ?? "", item?.live ? el("span", { class: "dropdown-live" }, "· Live") : null];
  }

  render() {
    const current = this.items.find(i => i.value === this.selected) ?? this.items[0];
    this.button = el("button", {
      type: "button", class: "dropdown-button", "aria-haspopup": "listbox", "aria-expanded": "false",
      "aria-controls": `${this.id}-list`, "aria-label": `${this.label}: ${current?.label ?? ""}${current?.live ? ", live" : ""}`,
      onclick: () => (this.isOpen ? this.close() : this.open()),
      onkeydown: e => {
        if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) { e.preventDefault(); this.open(); }
      },
    }, el("span", { class: "dropdown-value" }, Dropdown.#text(current)), el("span", { class: "dropdown-caret", "aria-hidden": "true" }));

    this.list = el("ul", {
      id: `${this.id}-list`, class: "dropdown-list", role: "listbox", tabindex: "-1", hidden: true,
      "aria-label": this.label, style: { "--visible": Dropdown.VISIBLE },
      onkeydown: e => this.#onKey(e),
      onfocusout: e => { if (!this.root.contains(e.relatedTarget)) this.close(false); },
    }, this.items.map((item, i) => el("li", {
      id: `${this.id}-${i}`, role: "option", class: "dropdown-item",
      "aria-selected": String(item.value === this.selected),
      onmousemove: () => this.#setActive(i, false),
      onclick: () => this.#pick(i),
    }, Dropdown.#text(item))));

    this.root = el("div", { class: "dropdown" }, this.button, this.list);
    return this.root;
  }

  get isOpen() { return !this.list.hidden; }

  open() {
    this.list.hidden = false;
    this.button.setAttribute("aria-expanded", "true");
    this.active = Math.max(0, this.items.findIndex(i => i.value === this.selected));
    this.#setActive(this.active);
    this.list.focus();
    // Close on any click outside the drop-down.
    this.outside = e => { if (!this.root.contains(e.target)) this.close(false); };
    document.addEventListener("pointerdown", this.outside);
  }

  close(focusButton = true) {
    if (!this.isOpen) return;
    this.list.hidden = true;
    this.button.setAttribute("aria-expanded", "false");
    document.removeEventListener("pointerdown", this.outside);
    if (focusButton) this.button.focus();
  }

  #setActive(i, scroll = true) {
    this.active = Math.min(this.items.length - 1, Math.max(0, i));
    [...this.list.children].forEach((li, n) => li.classList.toggle("active", n === this.active));
    this.list.setAttribute("aria-activedescendant", `${this.id}-${this.active}`);
    if (scroll) this.list.children[this.active].scrollIntoView({ block: "nearest" });
  }

  #pick(i) {
    const item = this.items[i];
    this.close();
    if (item.value !== this.selected) this.onPick(item.value);
  }

  #onKey(e) {
    const moves = {
      ArrowDown: this.active + 1, ArrowUp: this.active - 1, Home: 0, End: this.items.length - 1,
      PageDown: this.active + Dropdown.VISIBLE, PageUp: this.active - Dropdown.VISIBLE,
    };
    if (e.key in moves) { e.preventDefault(); this.#setActive(moves[e.key]); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this.#pick(this.active); }
    else if (e.key === "Escape") { e.preventDefault(); this.close(); }
    else if (e.key === "Tab") this.close(false);
  }
}
