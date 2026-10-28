/* The board's graph canvas (ruling 100): Cytoscape with the cola layout, as the old
   estate's graph page used them, fed by the page's own data: the inline answer
   (graph.answer) for the first view, then /graph.json, on the board itself, as the
   reader taps. Round nodes coloured by register with the label beneath, the centre
   ringed; soft curved edges in the key's colours, a near verdict dashed. Tap a node
   to grow its one hop, tap it again to fold it; double-tap to open its pane; drag,
   zoom, pan; "spread" runs cola, "tree" returns every node to its layered place.
   Ruling 105, the entity state (the answer's mode "entities"): an entity, one node per
   group of the links lane, is a rounded square labelled with its name and its count,
   a contested one with a dashed border; a lone row a circle with a dotted border.
   Tap an entity to open it as a compound node, its rows inside it in their register
   colours joined by the links that gathered them, labelled with the rule; tap it
   again to close it. A near line carries its reason on the line.
   Colours of the page come from the one stylesheet (read off the canvas's box);
   the nodes' and edges' come with the data (catalogue). Text goes in by
   textContent only. Nothing here asks anything of any other address.
   Ruling 108 (4): on the search tab the same canvas sits in a pane beside the results
   (#side), empty until a result is clicked; the click asks /graph.json centred on that
   row or entity, in the state the address carries, and mounts the canvas afresh. A
   result's links other than its title keep their own work, and a click with a key held
   opens the title's pane as before.
   Ruling 106 (2), the links lane's related grade: a lineage frame, a compound node in the
   lime of the key's "lineage" line with a double border (the near colour and dash stay
   near's alone), labelled with the relation and the years, around the companies in date
   order left to right (each its own node, never one entity) and the people on both,
   drawn once beneath them; a tap on the frame does nothing, its members tap as ever; a
   grown hop that brings a frame for nodes already drawn moves them into it, and a frame
   folded away lets its members go rather than taking them with it. */
(function () {
  "use strict";
  var holder = document.getElementById("cy");
  var source = document.getElementById("graph-data");
  if (!holder || !source || typeof cytoscape === "undefined") return;
  if (typeof cytoscapeCola !== "undefined") { try { cytoscape.use(cytoscapeCola); } catch (e) { /* registered already */ } }
  var tip = document.getElementById("tip");
  var cy = null;

  function mount(first) {
  if (cy) { cy.destroy(); cy = null; }
  holder.parentNode.classList.add("on");          // the canvas shows only once this runs; <noscript> holds the SVG
  var sheet = getComputedStyle(holder);
  var ink = sheet.color, surface = sheet.backgroundColor, accent = sheet.outlineColor;

  // which views (a tap's answer, or the first) brought each element: an element stays while one of them is open
  var by = {};                                     // id -> {source id: true}
  var grown = {};                                  // node id -> true while its one hop is open
  var BASE = "\u0000first";

  var people = first.mode === "entities";
  var opened = {};                                 // entity id -> true while its rows are open inside it
  function nodeData(n) {
    var d = { id: n.id, label: n.title, name: n.title, colour: n.colour, register: n.register_name, family: n.family, view: n.view,
              pane: n.pane, grow: n.grow, tx: n.x, ty: n.y, matched: n.matched, centre: n.centre, kind: n.kind || "row" };
    if (n.kind === "lineage") {
      d.shared = n.shared_people; d.drawnPeople = n.people_drawn; d.hidden = n.hidden; d.cut = n.cut;
    }
    if (n.stands_for) d.stands = n.stands_for;
    if (n.kind === "entity") {
      d.label = n.title + "\n" + n.count;
      d.count = n.count; d.open = n.open; d.contested = !!n.contested;
    }
    if (n.parent) d.parent = n.parent;
    return d;
  }
  function edgeData(e) {
    var d = { id: e.id, source: e.source, target: e.target, colour: e.colour, kind: e.kind,
              words: e.words, title: e.title, causes: e.causes, decisions: e.decisions || [] };
    if ((people && (e.dashed || e.inner)) || e.kind === "lineage") d.label = e.words;     // a near line's reason, an opened entity's rule, a relation
    return d;
  }
  // the node colours on the canvas now, by family of register, each family's registers on hover
  var legend = document.getElementById("legend");
  function relegend() {
    var seen = {}, order = [];
    cy.nodes().forEach(function (n) {
      if (n.data("kind") === "lineage") return;       // a frame is no register's
      var f = n.data("family");
      if (!seen[f]) { seen[f] = { colour: n.data("colour"), registers: {} }; order.push(f); }
      seen[f].registers[n.data("register")] = true;
    });
    legend.textContent = "";
    order.sort().forEach(function (f) {
      var s = document.createElement("span"), w = document.createElement("span");
      w.className = "swatch";
      w.style.backgroundColor = seen[f].colour;
      s.title = Object.keys(seen[f].registers).sort().join("; ");
      s.appendChild(w);
      s.appendChild(document.createTextNode(f));
      legend.appendChild(s);
    });
  }
  function own(id, from) { (by[id] = by[id] || {})[from] = true; }

  cy = cytoscape({
    container: holder,
    elements: [],
    minZoom: 0.1, maxZoom: 4,
    style: [
      { selector: "node", style: {
          "background-color": "data(colour)", width: 22, height: 22,
          label: "data(label)", "font-size": "10px", color: ink,
          "text-valign": "bottom", "text-halign": "center", "text-margin-y": 4,
          "text-wrap": "ellipsis", "text-max-width": "96px",
          "text-outline-color": surface, "text-outline-width": 2,
          "border-width": 1, "border-color": surface } },
      { selector: "node[?matched]", style: { width: 28, height: 28 } },
      { selector: "node[?centre]", style: { width: 34, height: 34, "border-width": 4, "border-color": ink } },
      { selector: "node.grown", style: { "border-width": 3, "border-color": accent } },
      { selector: "node:selected", style: { "border-width": 3, "border-color": ink } },
      { selector: "node[kind = \"entity\"]", style: { shape: "round-rectangle", width: 34, height: 34, "text-wrap": "wrap",
          "border-width": 3, "border-color": ink } },
      { selector: "node[?contested]", style: { "border-style": "dashed", "border-color": accent, "border-width": 4 } },
      { selector: "node[kind = \"lone\"]", style: { "border-style": "dotted", "border-width": 2, "border-color": ink } },
      { selector: "node[kind = \"child\"]", style: { width: 18, height: 18 } },
      { selector: "node:parent", style: { "background-opacity": 0.14, "text-valign": "top", "text-margin-y": -4,
          padding: 14, "border-width": 2, "border-color": ink } },
      { selector: "node[kind = \"lineage\"]", style: { shape: "round-rectangle", "background-color": "data(colour)",
          "background-opacity": 0.10, "border-style": "double", "border-width": 6, "border-color": "data(colour)",
          "text-valign": "top", "text-halign": "center", "text-margin-y": -6, "font-size": "11px", "font-weight": "bold",
          "text-wrap": "wrap", "text-max-width": "320px", padding: 22, width: 40, height: 40 } },
      { selector: "edge", style: {
          width: 2, "line-color": "data(colour)", "curve-style": "unbundled-bezier",
          "control-point-distances": 18, "control-point-weights": 0.5, "line-opacity": 0.9 } },
      { selector: "edge[?dashed]", style: { "line-style": "dashed", "line-dash-pattern": [6, 4] } },
      { selector: "edge[kind = \"lineage\"]", style: { width: 3, "control-point-distances": -34, "target-arrow-shape": "triangle",
          "target-arrow-color": "data(colour)", "arrow-scale": 1.1 } },
      { selector: "edge.hover", style: { width: 4, "line-opacity": 1 } },
      { selector: "edge[label]", style: { label: "data(label)", "font-size": "8px", color: ink, "text-rotation": "autorotate",
          "text-outline-color": surface, "text-outline-width": 2, "text-wrap": "ellipsis", "text-max-width": "140px" } }
    ]
  });

  // one answer's nodes and lines added, each new node placed near `at` by its layered offset from the answer's centre
  function merge(data, from, at) {
    var centre = null;
    data.nodes.forEach(function (n) { if (n.centre) centre = n; });
    var added = [];
    data.nodes.forEach(function (n) {
      own(n.id, from);
      if (!cy.getElementById(n.id).empty()) return;
      var d = nodeData(n), p = { x: n.x, y: n.y };
      if (at && centre) {
        p = { x: at.x + (n.x - centre.x) * 0.7, y: at.y + (n.y - centre.y) * 0.7 };
        d.tx = p.x; d.ty = p.y;                   // its layered place, for "tree", is where its answer put it
      }
      added.push({ group: "nodes", data: d, position: p });
    });
    data.edges.forEach(function (e) {
      own(e.id, from);
      if (!cy.getElementById(e.id).empty()) return;
      var d = edgeData(e);
      d.dashed = e.dashed;
      added.push({ group: "edges", data: d });
    });
    cy.add(added);
    data.nodes.forEach(function (n) {                // a frame this answer brings around nodes drawn before it
      if (!n.parent) return;
      var el = cy.getElementById(n.id), frame = cy.getElementById(n.parent);
      if (!el.empty() && !frame.empty() && el.data("parent") !== n.parent && !el.isParent()) el.move({ parent: n.parent });
    });
    relegend();
  }

  // fold: every element only `from` brought leaves; a grown node that leaves folds too
  function fold(from) {
    var queue = [from];
    while (queue.length) {
      var f = queue.shift();
      delete grown[f];
      cy.getElementById(f).removeClass("grown");
      Object.keys(by).forEach(function (id) {
        if (!by[id][f]) return;
        delete by[id][f];
        if (Object.keys(by[id]).length) return;
        delete by[id];
        var el = cy.getElementById(id);
        if (el.empty()) return;
        if (el.isNode() && grown[id]) queue.push(id);
        if (el.isNode() && el.data("kind") === "lineage") el.children().move({ parent: null });     // its members may stay
        el.remove();
      });
    }
    relegend();
  }

  // an entity opened as a compound node: its rows inside it, joined by the links that gathered them; tapped again, closed
  function toggleOpen(node) {
    var id = node.id();
    if (opened[id]) {
      delete opened[id];
      cy.remove(node.children());
      node.data("label", node.data("name") + "\n" + node.data("count"));
      relegend();
      return;
    }
    opened[id] = true;
    fetch(node.data("open"), { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        if (!opened[id] || cy.getElementById(id).empty()) return;
        var at = node.position(), n = data.nodes.length, r = 30 + 9 * Math.sqrt(n), added = [];
        data.nodes.forEach(function (c, i) {
          if (!cy.getElementById(c.id).empty()) return;
          var a = 2 * Math.PI * i / Math.max(n, 1), d = nodeData(c);
          d.parent = id;
          added.push({ group: "nodes", data: d, position: { x: at.x + r * Math.cos(a), y: at.y + r * Math.sin(a) } });
        });
        data.edges.forEach(function (e) {
          if (!cy.getElementById(e.id).empty()) return;
          var d = edgeData(e);
          d.dashed = e.dashed;
          added.push({ group: "edges", data: d });
        });
        cy.add(added);
        node.data("label", node.data("name") + " \u00b7 " + (data.shown < data.total ? data.shown + " of " + data.total + " rows drawn" : node.data("count")));
        relegend();
      })
      .catch(function () { delete opened[id]; say("the board could not open " + node.data("name")); });
  }

  function grow(node) {
    var id = node.id();
    if (grown[id]) { fold(id); return; }
    grown[id] = true;
    node.addClass("grown");
    fetch(node.data("grow"), { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        if (!grown[id]) return;                     // folded again before the answer came
        merge(data, id, node.position());
      })
      .catch(function () { delete grown[id]; node.removeClass("grown"); say("the board could not answer for " + node.data("label")); });
  }

  function say(text) {
    tip.textContent = text;
    tip.hidden = false;
    tip.style.left = "1rem"; tip.style.top = "1rem";
  }

  // fit the whole graph, never closer than FIT_ZOOM, so a graph of three rows is not drawn as large as the box
  var FIT_ZOOM = 1.4;
  function fitAll() {
    cy.fit(cy.elements(), 30);
    if (cy.zoom() > FIT_ZOOM) { cy.zoom(FIT_ZOOM); cy.center(); }
  }

  function tree() {
    cy.nodes().forEach(function (n) { if (n.data("kind") === "lineage") return; n.animate({ position: { x: n.data("tx"), y: n.data("ty") } }, { duration: 400 }); });
    setTimeout(fitAll, 430);
  }

  function spread() {
    var run = cy.layout({ name: "cola", animate: true, randomize: false, fit: true, padding: 30,
                          maxSimulationTime: 1500, nodeSpacing: 18, edgeLength: 110 });
    run.one("layoutstop", fitAll);
    run.run();
  }

  function showTip(evt, lines) {
    tip.textContent = "";
    lines.forEach(function (t, i) {
      var p = document.createElement(i ? "div" : "strong");
      p.textContent = t;
      tip.appendChild(p);
    });
    var box = holder.getBoundingClientRect(), at = evt.renderedPosition || { x: 0, y: 0 };
    tip.style.left = Math.min(at.x + 14, box.width - 260) + "px";
    tip.style.top = (at.y + 14) + "px";
    tip.hidden = false;
  }

  cy.on("onetap", "node", function (evt) {
    var k = evt.target.data("kind");
    if (k === "entity") toggleOpen(evt.target);
    else if (k !== "child" && k !== "lineage") grow(evt.target);
  });
  cy.on("dbltap", "node", function (evt) { if (evt.target.data("pane")) window.location.href = evt.target.data("pane"); });
  cy.on("mouseover", "edge", function (evt) {
    var e = evt.target;
    e.addClass("hover");
    var lines = [e.data("words")];
    e.data("causes").forEach(function (c) {
      lines.push(c.kind + ": " + c.words + (c.rule ? " " + c.rule : ""));
      (c.rows || []).slice(0, 6).forEach(function (p) { lines.push("  rows: " + p[0] + " \u2014 " + p[1]); });
      if (c.rows && c.rows.length > 6) lines.push("  and " + (c.rows.length - 6) + " more pairs of rows");
    });
    showTip(evt, lines.concat(e.data("decisions")));
  });
  cy.on("mouseout", "edge", function (evt) { evt.target.removeClass("hover"); tip.hidden = true; });
  cy.on("mouseover", "node", function (evt) {
    var n = evt.target;
    var k = n.data("kind"), how;
    if (k === "lineage") {
      showTip(evt, [n.data("name"), "a relation the links lane found, never one entity: each company is its own node, in date order of registration",
                    n.data("shared") + " people on both" + (n.data("drawnPeople") < n.data("shared") ? ", " + n.data("drawnPeople") + " drawn" : "") +
                    (n.data("hidden") ? "; " + n.data("hidden") + " whose name is suppressed, not drawn" : "")]);
      return;
    }
    if (k === "entity") how = [n.data("count") + (n.data("contested") ? "; contested: the watch flagged this group" : ""),
                               "the name is the fullest filed among its rows, not a link",
                               opened[n.id()] ? "tap to close its rows" : "tap to open its rows; double-tap to open its pane"];
    else if (k === "child") how = ["a row of this entity; double-tap to open its pane"];
    else how = [(k === "lone" ? "a lone row: in no group" : k === "apart" ? "kept apart: its name is suppressed" : n.data("register") + " \u00b7 " + n.data("view")),
                grown[n.id()] ? "tap to fold its one hop" : "tap to grow its one hop; double-tap to open its pane"];
    if (n.data("stands")) how.unshift("one person on both companies: stands for " + n.data("stands") + " rows");
    showTip(evt, [n.data("name"), n.data("register") + " \u00b7 " + n.data("view")].concat(how));
  });
  cy.on("mouseout", "node", function () { tip.hidden = true; });

  document.getElementById("spread").onclick = spread;
  document.getElementById("tree").onclick = tree;

  merge(first, BASE, null);
  fitAll();
  window.boardGraph = cy;                           // for a look from the browser's console, and the headless check
  }

  var side = document.getElementById("side"), results = document.getElementById("results");
  if (!side || !results) { mount(JSON.parse(source.textContent)); return; }

  // ruling 108 (4): a result clicked opens its graph beside the results
  var title = document.getElementById("side-title"), pane = document.getElementById("side-pane"),
      tab = document.getElementById("side-tab"), asked = 0;
  function open(hit) {
    var mine = ++asked, row = hit.querySelector("a.row");
    Array.prototype.forEach.call(results.querySelectorAll("article.hit.on"), function (a) { a.classList.remove("on"); });
    hit.classList.add("on");
    side.classList.add("on");
    title.textContent = row ? row.textContent : "Graph";
    pane.href = row ? row.getAttribute("href") : "#";
    tab.href = hit.getAttribute("data-graph").replace("/graph.json?", "/graph?");
    side.scrollIntoView({ block: "nearest" });
    fetch(hit.getAttribute("data-graph"), { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { if (mine === asked) mount(data); })
      .catch(function () { if (mine === asked) say("the board could not answer for " + title.textContent); });
  }
  results.addEventListener("click", function (evt) {
    if (evt.button !== 0 || evt.ctrlKey || evt.metaKey || evt.shiftKey || evt.altKey) return;
    var hit = evt.target.closest("article.hit[data-graph]");
    if (!hit) return;
    var a = evt.target.closest("a");
    if (a && a !== hit.querySelector("a.row")) return;   // a source, a citation or a far row keeps its own link
    evt.preventDefault();
    open(hit);
  });
  document.getElementById("side-close").onclick = function () {
    side.classList.remove("on");
    Array.prototype.forEach.call(results.querySelectorAll("article.hit.on"), function (a) { a.classList.remove("on"); });
  };
})();
