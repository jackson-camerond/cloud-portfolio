// main.js — deliberately tiny. Its job is to prove you can wire up behavior,
// not to ship a framework. It runs on every page that includes it.

// Auto-update the copyright year so the footer never goes stale.
const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}
