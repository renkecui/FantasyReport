export class Dom {
  /** Dom.el("td", { class: "x", title: "y", onclick: fn, style: { "--h": 120 } }, child, "text", ...) */
  static el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "style") for (const [p, val] of Object.entries(v)) node.style.setProperty(p, val);
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      node.append(c instanceof Node ? c : String(c));
    }
    return node;
  }
}
