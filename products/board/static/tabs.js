// The board's tabs keep their place (Arthur, 9 November 2026: "we need it to maintain state - that's what a tab is").
// Each tab's state is its address. On every page the address of the tab that is on is kept in this browser's
// sessionStorage, under the tab's name; every other tab's link is pointed at the address that tab was last on, so
// going back to a tab returns to the search, the rows or the memo it showed. Nothing leaves the browser; a new
// browser window starts every tab fresh. A tab never visited keeps the address the page gave it.
(function () {
  "use strict";
  var KEY = "qv4-board-tab:";
  var store;
  try { store = window.sessionStorage; } catch (e) { return; }
  if (!store) { return; }
  var links = document.querySelectorAll("nav.tabs a[data-tab]");
  var here = window.location.pathname + window.location.search;
  for (var i = 0; i < links.length; i++) {
    var a = links[i];
    var name = a.getAttribute("data-tab");
    if (a.classList.contains("on")) {
      try { store.setItem(KEY + name, here); } catch (e) { /* storage full or refused: the tab still works */ }
      continue;
    }
    var kept = null;
    try { kept = store.getItem(KEY + name); } catch (e) { kept = null; }
    if (kept && kept.charAt(0) === "/" && kept.charAt(1) !== "/") {   // only this board's own addresses
      a.setAttribute("href", kept);
    }
  }
})();
