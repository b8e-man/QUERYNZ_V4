// The board's chat pane, the reader's part (ruling 122): the thread lives in
// this browser tab's sessionStorage and is posted whole with each new
// question to the board's own /chat (same origin, JSON); the answer comes
// back as parts, text and citations, built here as text nodes and links, so
// no HTML from the answer is ever parsed. A citation opens its row's pane in
// the main page; one naming no row is struck, "not a row". The pane never
// blocks the page. No library.
(function () {
  "use strict";
  var KEY = "qv4-board-chat";
  var pane = document.getElementById("chat");
  var box = document.getElementById("chat-thread");
  var form = document.getElementById("chat-form");
  var q = document.getElementById("chat-q");
  var ask = document.getElementById("chat-ask");
  var fresh = document.getElementById("chat-new");
  if (!pane || !box || !form || !q) return;
  var thread = [];
  try { thread = JSON.parse(window.sessionStorage.getItem(KEY) || "[]") || []; } catch (e) { thread = []; }
  if (!Array.isArray(thread)) thread = [];

  function keep() {
    try { window.sessionStorage.setItem(KEY, JSON.stringify(thread)); } catch (e) { /* storage refused: the thread lasts the page */ }
  }

  function partsOf(turn) {
    if (Array.isArray(turn.parts) && turn.parts.length) return turn.parts;
    return [{ t: turn.content || "" }];
  }

  function draw(turn) {
    var div = document.createElement("div");
    div.className = "turn " + (turn.role === "user" ? "user" : turn.role === "assistant" ? "assistant" : "note");
    partsOf(turn).forEach(function (p) {
      if (p.c && p.href) {
        var a = document.createElement("a");
        a.className = "cite row";
        a.href = p.href;
        a.textContent = "[" + p.c + "]";
        div.appendChild(a);
      } else if (p.x) {
        var s = document.createElement("s");
        s.className = "cite";
        s.textContent = "[" + p.x + "] not a row";
        div.appendChild(s);
      } else {
        div.appendChild(document.createTextNode(p.t || ""));
      }
    });
    if (turn.seconds !== undefined && turn.role === "assistant") {
      var w = document.createElement("span");
      w.className = "when";
      w.textContent = turn.seconds + " s" + (turn.tools && turn.tools.length ? " · " + turn.tools.join(", ") : "");
      div.appendChild(w);
    }
    box.appendChild(div);
    return div;
  }

  function redraw() {
    while (box.firstChild) box.removeChild(box.firstChild);
    thread.forEach(draw);
    box.scrollTop = box.scrollHeight;
  }

  function posted() {
    // only the questions and the model's own answers go back; the pane's notes stay in the tab
    return thread.filter(function (t) { return t.role === "user" || t.role === "assistant"; })
      .map(function (t) { return { role: t.role, content: t.content }; });
  }

  function busy(on) {
    if (ask) ask.disabled = on;
    q.disabled = on;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = (q.value || "").trim();
    if (!text) return;
    thread.push({ role: "user", content: text });
    keep();
    redraw();
    q.value = "";
    var wait = draw({ role: "note", content: "asking the model…" });
    box.scrollTop = box.scrollHeight;
    busy(true);
    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread: posted() }),
      credentials: "same-origin"
    }).then(function (r) { return r.json(); }).then(function (a) {
      if (a && a.ok) {
        thread.push({ role: "assistant", content: a.answer || "", parts: a.parts, seconds: a.seconds, tools: a.tools });
      } else {
        thread.push({ role: "note", content: (a && a.answer) || "the chat model is not running" });
      }
    }).catch(function () {
      thread.push({ role: "note", content: "the board did not answer the chat" });
    }).then(function () {
      if (wait && wait.parentNode) wait.parentNode.removeChild(wait);
      keep();
      redraw();
      busy(false);
      q.focus();
    });
  });

  q.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      if (typeof form.requestSubmit === "function") form.requestSubmit(); else form.dispatchEvent(new Event("submit", { cancelable: true }));
    }
  });

  if (fresh) {
    fresh.addEventListener("click", function () {
      thread = [];
      keep();
      redraw();
      q.focus();
    });
  }

  redraw();
})();
