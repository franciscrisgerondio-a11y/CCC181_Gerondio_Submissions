// Court dropdown on the join form: put the chosen court into the hidden field and the toggle label.
function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

document.querySelectorAll(".court-select").forEach((root) => {
  const input = root.querySelector("input[type=hidden]");
  const current = root.querySelector(".court-current");
  const toggle = root.querySelector(".court-toggle");
  const items = root.querySelectorAll(".court-item");

  items.forEach((item) => {
    item.addEventListener("click", () => {
      input.value = item.dataset.value;
      items.forEach((i) => {
        i.classList.toggle("active", i === item);
        i.setAttribute("aria-current", i === item ? "true" : "false");
      });
      current.replaceChildren(
        el("span", "court-name", item.dataset.name),
        el("span", "court-wait", item.dataset.wait)
      );
      toggle.classList.remove("is-invalid");
    });
  });
});

// Staff court filter: submit as soon as a court is chosen.
document.querySelectorAll("[data-autosubmit]").forEach((select) => {
  select.addEventListener("change", () => select.form.submit());
});