/* The board's graph canvas (ruling 100): Cytoscape with the cola layout, as the old
   estate's graph page used them, fed by the page's own data: the inline answer
   (graph.answer) for the first view, then /graph.json, on the board itself, as the
   reader taps. Round nodes coloured by register with the label beneath, the centre
   ringed; soft curved edges in the key's colours, a near verdict dashed. Tap a node
   to grow its one hop, tap it again to fold it; double-tap to open its pane; drag,
   zoom, pan; "spread" runs cola, "tree" returns every node to its layered place.
   Colours of the page come from the one stylesheet (read off the canvas's box);
   the nodes' and edges' come with the data (catalogue). Text goes in by
   textContent only. Nothing here asks anything of any other address. */
(function () {
  "use strict";
  var holder = document.getElementById("cy");
  var source = document.getElementById("graph-data");
  if (!holder || !source || typeof cytoscape === "undefined") return;
  if (typeof cytoscapeCola !== "undefined") { try { cytoscape.use(cytoscapeCola); } catch (e) { /* registered already */ } }
  var first = JSON.parse(source.textContent);
  holder.parentNode.classList.add("on");          // the canvas shows only once this runs; <noscript> holds the SVG
  var sheet = getComputedStyle(holder);
  var ink = sheet.color, surface = sheet.backgroundColor, accent = sheet.outlineColor;
  var tip = document.getElementById("tip");

  // which views (a tap's answer, or the first) brought each element: an element stays while one of them is open
  var by = {};                                     // id -> {source id: true}
  var grown = {};                                  // node id -> true while its one hop is open
  var BASE = "\u0000first";

  function nodeData(n) {
    return { id: n.id, label: n.title, colour: n.colour, register: n.register_name, family: n.family, view: n.view,
             pane: n.pane, grow: n.grow, tx: n.x, ty: n.y, matched: n.matched, centre: n.centre };
  }
  function edgeData(e) {
    return { id: e.id, source: e.source, target: e.target, colour: e.colour, kind: e.kind,
             words: e.words, title: e.title, causes: e.causes };
  }
  // the node colours on the canvas now, by family of register, each family's registers on hover
  var legend = document.getElementById("legend");
  function relegend() {
    var seen = {}, order = [];
    cy.nodes().forEach(function (n) {
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

  var cy = cytoscape({
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
      { selector: "edge", style: {
          width: 2, "line-color": "data(colour)", "curve-style": "unbundled-bezier",
          "control-point-distances": 18, "control-point-weights": 0.5, "line-opacity": 0.9 } },
      { selector: "edge[?dashed]", style: { "line-style": "dashed", "line-dash-pattern": [6, 4] } },
      { selector: "edge.hover", style: { width: 4, "line-opacity": 1 } }
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
        el.remove();
      });
    }
    relegend();
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
    cy.nodes().forEach(function (n) { n.animate({ position: { x: n.data("tx"), y: n.data("ty") } }, { duration: 400 }); });
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

  cy.on("onetap", "node", function (evt) { grow(evt.target); });
  cy.on("dbltap", "node", function (evt) { window.location.href = evt.target.data("pane"); });
  cy.on("mouseover", "edge", function (evt) {
    var e = evt.target;
    e.addClass("hover");
    showTip(evt, [e.data("words")].concat(e.data("causes").map(function (c) {
      return c.kind + ": " + c.words + (c.rule ? " " + c.rule : "");
    })));
  });
  cy.on("mouseout", "edge", function (evt) { evt.target.removeClass("hover"); tip.hidden = true; });
  cy.on("mouseover", "node", function (evt) {
    var n = evt.target;
    showTip(evt, [n.data("label"), n.data("register") + " · " + n.data("view"),
                  grown[n.id()] ? "tap to fold its one hop" : "tap to grow its one hop; double-tap to open its pane"]);
  });
  cy.on("mouseout", "node", function () { tip.hidden = true; });

  document.getElementById("spread").addEventListener("click", spread);
  document.getElementById("tree").addEventListener("click", tree);

  merge(first, BASE, null);
  fitAll();
  window.boardGraph = cy;                           // for a look from the browser's console, and the headless check
})();
