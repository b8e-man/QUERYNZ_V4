// The board's register table, the reader's part (ruling 117 (3)): the rows'
// height (one line clipped, three lines wrapped, whole values wrapped) and
// each column's width, dragged at its heading's right edge (the CSS resize
// handle), kept for this browser session alone in sessionStorage, one entry
// per view. Nothing is sent and nothing is written; the sort is the server's,
// in the address. No library.
(function () {
  "use strict";
  var table = document.querySelector("table.grid[data-view]");
  var lines = document.getElementById("table-lines");
  if (!table) return;
  var key = "qv4-board-table:" + table.getAttribute("data-view");
  var saved = {};
  try { saved = JSON.parse(window.sessionStorage.getItem(key) || "{}") || {}; } catch (e) { saved = {}; }

  function keep() {
    try { window.sessionStorage.setItem(key, JSON.stringify(saved)); } catch (e) { /* storage refused: the choice lasts the page */ }
  }

  function setLines(value) {
    if (["1", "3", "all"].indexOf(value) < 0) value = "1";
    table.setAttribute("data-lines", value);
    if (lines) lines.value = value;
  }

  setLines(saved.lines || "1");
  if (lines) {
    lines.addEventListener("change", function () {
      saved.lines = lines.value;
      setLines(lines.value);
      keep();
    });
  }

  var widths = saved.widths || {};
  var heads = table.querySelectorAll("th[data-col] > div.th");
  Array.prototype.forEach.call(heads, function (div) {
    var col = div.parentNode.getAttribute("data-col");
    if (widths[col]) div.style.width = widths[col] + "px";
  });
  if (!window.ResizeObserver) return;
  var ready = false;
  var watch = new ResizeObserver(function (entries) {
    if (!ready) return;                       // the first call reports the widths as laid out, not a drag
    entries.forEach(function (entry) {
      var col = entry.target.parentNode.getAttribute("data-col");
      widths[col] = Math.round(entry.target.getBoundingClientRect().width);
    });
    saved.widths = widths;
    keep();
  });
  Array.prototype.forEach.call(heads, function (div) { watch.observe(div); });
  window.requestAnimationFrame(function () { ready = true; });
})();
