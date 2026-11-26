// The review tab's list sets (products/board/review.py, a set with "mode": "list"): every row judged where it stands,
// with no page load. A click on a choice, or its key on the row in focus (J junk, W wrong kind, K keep, L closer look),
// sends the one answer and moves to the next row not judged; the arrow keys move between rows.
(function () {
  var list = document.getElementById("rl-list");
  if (!list) return;
  var set = list.getAttribute("data-set");
  var keys = {};
  list.querySelectorAll(".rl-row:first-child button[data-choice]").forEach(function (b) { keys[b.getAttribute("data-k")] = b.getAttribute("data-choice"); });
  var left = document.getElementById("rl-left");
  function rows() { return Array.prototype.slice.call(list.querySelectorAll(".rl-row")); }
  function next(from) {
    var all = rows(), i = all.indexOf(from);
    for (var j = i + 1; j < all.length; j++) if (!all[j].getAttribute("data-was")) return all[j];
    return all[i + 1] || null;
  }
  function judge(row, choice) {
    var body = "set=" + encodeURIComponent(set) + "&q=" + encodeURIComponent(row.getAttribute("data-q")) + "&choice=" + encodeURIComponent(choice);
    row.classList.add("rl-sending");
    fetch("/review/answer", {method: "POST", redirect: "manual", headers: {"Content-Type": "application/x-www-form-urlencoded"}, body: body})
      .then(function (r) {
        row.classList.remove("rl-sending");
        if (r.type === "opaqueredirect" || r.ok) {
          var was = row.getAttribute("data-was");
          row.setAttribute("data-was", choice);
          row.className = "rl-row rl-" + choice;
          if (!was && left) left.textContent = String(Math.max(0, parseInt(left.textContent, 10) - 1));
        } else { row.classList.add("rl-failed"); }
      })
      .catch(function () { row.classList.remove("rl-sending"); row.classList.add("rl-failed"); });
    var n = next(row);
    if (n) { n.focus(); n.scrollIntoView({block: "center"}); }
  }
  list.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-choice]");
    if (b) { e.preventDefault(); judge(b.closest(".rl-row"), b.getAttribute("data-choice")); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var row = document.activeElement && document.activeElement.closest ? document.activeElement.closest(".rl-row") : null;
    if (!row) { if (e.key === "ArrowDown" || e.key === "j") { var f = rows().filter(function (r) { return !r.getAttribute("data-was"); })[0]; if (f) { e.preventDefault(); f.focus(); } } return; }
    var k = e.key.toLowerCase();
    if (keys[k]) { e.preventDefault(); judge(row, keys[k]); }
    else if (e.key === "ArrowDown") { var a = rows(), i = a.indexOf(row); if (a[i + 1]) { e.preventDefault(); a[i + 1].focus(); } }
    else if (e.key === "ArrowUp") { var b = rows(), m = b.indexOf(row); if (m > 0) { e.preventDefault(); b[m - 1].focus(); } }
  });
  var first = rows().filter(function (r) { return !r.getAttribute("data-was"); })[0];
  if (first) first.focus();
})();
