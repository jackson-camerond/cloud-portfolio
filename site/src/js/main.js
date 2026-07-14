// main.js — deliberately tiny. Its job is to prove you can wire up behavior,
// not to ship a framework. It runs on every page that includes it.

// Auto-update the copyright year so the footer never goes stale.
const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// Projects page: show every "Live" card, plus only the next N "Coming soon"
// cards in document order. The rest stay in the markup — projects.html is
// also a build log/memory block — they just don't render publicly until
// they're closer to shipping. Flipping a card from status-planned to
// status-live (the existing workflow) automatically promotes the next
// hidden "Coming soon" card into the visible window on the next page load.
const VISIBLE_PLANNED_COUNT = 3;
const projectCards = document.querySelectorAll(".project-card");
if (projectCards.length) {
  let plannedSeen = 0;
  projectCards.forEach((card) => {
    if (!card.querySelector(".status-planned")) return; // live cards always show
    plannedSeen += 1;
    if (plannedSeen > VISIBLE_PLANNED_COUNT) {
      card.hidden = true;
    }
  });
}
