// The review tab's keys (products/board/review.py): 1 to 9 answer, 0 "bad question", N a note, S skip, B back, Escape leaves the note.
(function () {
  var form = document.getElementById("rv-form");
  if (!form) return;
  var note = document.getElementById("rv-note");
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) {
      if (e.key === "Escape") t.blur();
      if (e.key === "Enter") e.preventDefault();   // a note never answers by itself: the answer is a choice
      return;
    }
    var k = e.key.toLowerCase();
    if (k >= "0" && k <= "9") {
      var b = form.querySelector('button[data-key="' + k + '"]');
      if (b) { e.preventDefault(); b.click(); }
    } else if (k === "n") {
      e.preventDefault(); note.focus();
    } else if (k === "s") {
      var s = document.getElementById("rv-skip"); if (s) location.href = s.href;
    } else if (k === "b") {
      var p = document.getElementById("rv-back"); if (p && p.getAttribute("href") !== "#") location.href = p.href;
    }
  });
})();
