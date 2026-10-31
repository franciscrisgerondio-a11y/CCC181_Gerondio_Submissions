const POLL_MS = 5000;

// Swap in new HTML only when it changed, and keep keyboard focus on the same button.
function swapKeepingFocus(container, html) {
  if (container.innerHTML.trim() === html.trim()) return;
  const active = document.activeElement;
  const key = active && container.contains(active) ? active.dataset.key : null;
  container.innerHTML = html;
  if (key) {
    const same = container.querySelector(`[data-key="${key}"]`);
    if (same && !same.disabled) same.focus();
  }
}

// Ask the server for a fresh piece of HTML every few seconds and swap it in.
function pollFragment(container) {
  const run = async () => {
    if (document.hidden) return;
    try {
      const res = await fetch(container.dataset.url, { headers: { "X-Requested-With": "fetch" } });
      if (res.ok) swapKeepingFocus(container, await res.text());
    } catch (err) {
      console.warn("Could not refresh", err);
    }
  };
  setInterval(run, POLL_MS);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) run(); });
}

// Your tickets strip and the "you are called" alert, on every page.
const myTickets = document.getElementById("my-tickets-live");
if (myTickets && myTickets.dataset.poll === "true") pollFragment(myTickets);

// Staff dashboard stays live as players join, leave and get called.
const staffLive = document.getElementById("staff-live");
if (staffLive) pollFragment(staffLive);

// Stop double joining: disable the button once the form is submitted.
const joinForm = document.getElementById("join-form");
if (joinForm) {
  joinForm.addEventListener("submit", () => {
    const button = joinForm.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = "Getting your ticket…";
  });

  // If the browser restores this page from its back/forward cache, unlock the button again.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      const button = joinForm.querySelector("button[type=submit]");
      button.disabled = false;
      button.innerHTML = 'Get a ticket <span aria-hidden="true">→</span>';
    }
  });
}

// Court dropdown on the join form.
function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

const waitText = (n) => `${n} ${n === 1 ? "group" : "groups"} waiting`;

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
      toggle.focus();
    });
  });

  // Keep the waiting counts on the join page live.
  const refreshCourts = async () => {
    if (document.hidden) return;
    try {
      const res = await fetch(root.dataset.url);
      if (!res.ok) return;
      const data = await res.json();

      data.courts.forEach((c) => {
        const item = root.querySelector(`.court-item[data-value="${c.id}"]`);
        if (!item) return;
        item.dataset.wait = waitText(c.waiting);
        item.querySelector(".court-wait").textContent = waitText(c.waiting);
        if (item.classList.contains("active")) {
          const shown = current.querySelector(".court-wait");
          if (shown) shown.textContent = waitText(c.waiting);
        }
      });

      const number = document.getElementById("hero-waiting-number");
      const label = document.getElementById("hero-waiting-label");
      if (number) number.textContent = data.waiting_total;
      if (label) label.textContent = data.waiting_total === 1 ? "group waiting" : "groups waiting";
    } catch (err) {
      console.warn("Could not refresh courts", err);
    }
  };
  setInterval(refreshCourts, POLL_MS);
});


document.addEventListener("submit", (event) => {
  const message = event.target.dataset && event.target.dataset.confirm;
  if (message && !confirm(message)) event.preventDefault();
});