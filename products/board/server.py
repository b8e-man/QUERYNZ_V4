"""The board's page, served on the local network only (design rule 7;
hard limit 13), with the least machinery that works: the standard
library's HTTP server, one page per request. Script runs on the search tab's
graph beside the results (rulings 100, 108, 111),
from the board's own /static/ files; every page carries a content security
policy that lets it ask nothing of any other address.
Routes:

  GET  /?q=<term>&p=<view:key|view:key|person:view:key…>&all=<0|1>&r=<register>…&first=&middle=&last=&address=&org=&year=
                    the search tab: the left pane (check boxes, the search box, the fields of the expanded search,
                    ruling 82), the results beside it with the near matches below them (ruling 83), then one pane per
                    step of the path; ruling 108: the results under one tab per field matched, in rows or entities
                    (`g=entities`), and an empty graph pane beside them that a click on a result fills from /graph.json
  GET  /?…&gv=1      ruling 111: the search page with the graph beside the results drawn now (the matching rows as
                    nodes, the connections their registers assert as edges, one hop; centred on `d` where given; a
                    Cytoscape canvas, ruling 100, with the SVG inside <noscript>)
  GET  /graph?q=&…&c=<view:key>   the graph tab's old address (the tab left the bar, ruling 111): a 303 to the
                    search page on the same query, boxes and state with the graph open (`gv=1`), centred on `c`; so
                    does `/?tab=graph…`
  GET  /graph.json?c=<view:key>&all=&r=…   the same graph as data (graph.answer): one row's one hop, for the canvas's taps
  GET  /dossier?d=<entity:group id|view:key>&q=&all=&r=…   the dossier's pane alone (ruling 110, dossier.py), which
                    graph.js puts under the graph when a result is clicked or a node tapped; `d=` on /
                    opens a page with that dossier under its graph, so a view reopens with it
  GET  /static/<name>  the board's own files (assets.FILES), with a long cache header; 404 for any other name
  GET  /pinned      the pinned panes       GET /saved     the saved paths
  POST /pin         pin a pane             POST /save     save the path walked
  GET  /doc/<sha256>  the captured document a row cites, its bytes read only from the store with its content type,
                    whatever its source (document.py, rulings 86 (4) and 88); 404 for anything else
  GET  /uses        the use cases tab (ruling 87): the plan's table, read at render time, with what the data holds for each;
                    each name opens its interface on its own server in a new browser tab (ruling 89)
  GET  /health      'ok' and the port, for the launcher

Every page's bar ends with the database's connections in use over its
maximum, by login on hover (ruling 90). The read connection is opened per
request and closed after; the two writes
go through products.board.state. Nothing in the estate is written."""
from __future__ import annotations

import contextlib
import http.server
import os
import socketserver
import sys
import threading
import urllib.parse

from support.docstore import landing as docstore
from products.board import assets
from products.board import catalogue as cat
from products.board import collapse, db, document, dossier, graph, lineage, links_view, near, panes, people, search, state, uses

PORT = int(os.environ.get("QV4_BOARD_PORT") or 8420)
BIND = os.environ.get("QV4_BOARD_BIND") or "0.0.0.0"   # the local network; never a public address (hard limit 13)
REPORT_URL = os.environ.get("QV4_REPORT_URL") or ""    # the subject report's server; unset, no pane offers a report
MAX_PANES = 12
RENDER_LOCK = threading.Lock()      # one page at a time: every session's bin/q shares the server's connections
#: every page asks nothing of any address but the board's own (ruling 100; hard limit 13): scripts only from /static/,
#: the page's data inline as JSON (never run), the canvas's taps to /graph.json
POLICY = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
          "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")


def counter(conn=None):
    """The nav bar's connection count (ruling 90), one query per page on the
    product reader (`conn` where the page already holds one); None when it
    fails, and the page still renders ("db ?")."""
    try:
        with (contextlib.nullcontext(conn) if conn is not None else db.scan_connect()) as c:
            return db.connections(c)
    except Exception:
        return None


def parse_path(p: str) -> list:
    steps = []
    for s in (p or "").split("|"):
        s = s.strip()
        if not s:
            continue
        if s.startswith(people.ENTITY):                # an entity of the people state (ruling 105): entity:<group id>
            if len(s) > len(people.ENTITY):
                steps.append(s[:300])
        elif s.startswith("person:"):
            _, view, key = s.split(":", 2)
            if view in cat.BY_NAME and key:
                steps.append(s)
        else:
            view, _, key = s.partition(":")
            if view in cat.BY_NAME and key:
                steps.append(s)
    return steps[:MAX_PANES]


def parse_centre(c: str) -> str:
    view, _, key = (c or "").strip().partition(":")
    return f"{view}:{key}" if view in cat.BY_NAME and key else ""


def resolver(conn):
    cache = {}

    def resolve(ref: str):
        if ref in cache:
            return cache[ref]
        register, key = links_view.split_ref(ref)
        v = links_view.view_for(conn, register, key) if register else None
        r = search.row(conn, v.name, key) if v else None
        cache[ref] = (v, r) if r else None
        return cache[ref]
    return resolve


def same_name_memo(conn):
    """One 'same name elsewhere' scan per row per request: a row's pane and
    its person pane share it."""
    memo = {}

    def same(v, r):
        k = (v.name, r["key"])
        if k not in memo:
            memo[k] = search.same_name(conn, v, r) if v.names else {}
        return memo[k]
    return same


def row_context(conn, v: cat.View, r: dict, q: str, path: list, pinned: set, same=None, boxes=None, docs=None,
                far=None) -> dict:
    same = same or same_name_memo(conn)
    ref = links_view.ref(v, r["key"])
    same_words = search.names_of_row(v, r)
    ctx = {"v": v, "row": r, "q": q, "path": path, "pinned": (v.name, r["key"]) in pinned,
           "parent": search.parent(conn, v, r), "children": search.children(conn, v, r),
           "doc_names": docstore.names_of(r["document"], conn) if r.get("document") else [],
           "links": links_view.links_of(conn, ref), "group": links_view.group_of(conn, ref) if v.kind == "person" else {},
           "same": same(v, r), "same_words": same_words, "resolve": resolver(conn),
           "report": panes.report_href(REPORT_URL, ref), "boxes": boxes,
           "docs": docs if docs is not None else document.statuses(conn, [r.get("document")]),
           "far": far if far is not None else search.far_rows(conn, [(v, r)])}
    return ctx


def person_context(conn, v: cat.View, r: dict, q: str, path: list, same=None, boxes=None) -> dict:
    same = same or same_name_memo(conn)
    ref = links_view.ref(v, r["key"])
    group = links_view.group_of(conn, ref)
    resolve = resolver(conn)
    members = []
    for other in group.get("rows") or []:
        if other == ref:
            continue
        hit = resolve(other)
        if hit:
            members.append(hit)
    return {"v": v, "row": r, "q": q, "path": path, "group": group, "members": members,
            "links": links_view.links_of(conn, ref), "same": same(v, r),
            "same_words": search.names_of_row(v, r), "resolve": resolve,
            "report": panes.report_href(REPORT_URL, ref), "boxes": boxes}


def entity_context(conn, group_id: str):
    """people.entity, with the near rows resolved for its pane (one query per view)."""
    ent = people.entity(conn, group_id)
    if ent is not None:
        others = {l["row_b"] if l["mine"] == l["row_a"] else l["row_a"] for l in ent["near"]}
        for l in ent.get("related") or []:                # ruling 106 (2): the other company and the people on both
            others |= {l["row_a"], l["row_b"]} | {p.get(k) for p in lineage.evidence(l).get("shared_rows") or []
                                                  for k in ("earlier", "later") if p.get(k)}
        ent["far"] = people.resolve_refs(conn, others - {ref for ref, _, _ in ent["rows"]})
    return ent


def dossier_of(conn, chosen: str, q: str, boxes) -> tuple:
    """(the dossier's pane, the row its graph centres on) for `chosen`
    (ruling 110); the placeholder graph.js fills, and no centre, when nothing is chosen."""
    if not chosen:
        return dossier.placeholder(q, boxes), ""
    x = dossier.gather(conn, chosen, REPORT_URL)
    if x["kind"] == "fold":                            # ruling 112: the graph centres on the fold's first member
        return dossier.pane(x, q, boxes), x["centre"] if not x["centre"].startswith(people.ENTITY) else ""
    centre = chosen if not chosen.startswith(people.ENTITY) and x["kind"] != "suppressed" else \
        next((f"{v.name}:{r['key']}" for _, v, r in x.get("rows") or ()), "")
    return dossier.pane(x, q, boxes), centre


def render_dossier(chosen: str, q: str = "", conn=None, boxes: search.Boxes = search.FIRST) -> str:
    """GET /dossier (ruling 110): the pane alone, on the session reader (the citations read the store's records)."""
    with RENDER_LOCK, (contextlib.nullcontext(conn) if conn is not None else db.read_connect()) as conn:
        return dossier_of(conn, dossier.parse(chosen), q, boxes)[0]


def render(q: str, path: list, message: str = "", conn=None, boxes: search.Boxes = search.FIRST, near_names: bool = False,
           chosen: str = "", graph_open: bool = False) -> str:
    """The search tab. `conn` is a session-reader connection to reuse (the
    check passes its own); without one a connection is opened and closed.
    `boxes`: the form's check boxes, carried on every href (ruling 81);
    `near_names`: the near-names pane beside the search pane (ruling 92 (4));
    `chosen` (`d=`), the entity or row whose dossier opens under the graph
    beside the results (ruling 110), the graph centred on it; `graph_open`
    (`gv=1`, ruling 111: the graph tab's old address lands here), the graph
    beside the results built now, centred on `chosen` or the whole search."""
    with RENDER_LOCK, (contextlib.nullcontext(conn) if conn is not None else db.read_connect()) as conn:
        held = db.pub_views(conn)
        regs = search.selection(boxes, search.held_registers(held))
        asked = boxes.asked()
        asking = bool(q or asked) and bool(regs)
        results = search.search(conn, q, limit=search.RESULTS_LIMIT, registers=regs, fields=asked, mode=boxes.mode,
                                removed=boxes.removed, tabs=True) if asking else {}
        nearby = near.near(conn, q, asked, registers=regs, held=held, mode=boxes.mode, removed=boxes.removed) if asking else None     # ruling 83, below the exact results
        pinned = {(p["view"], p["key"]) for p in state.pins(conn)}
        same = same_name_memo(conn)
        words = panes.search_words(q, boxes)
        steps = []
        for step in path:
            if step.startswith(people.ENTITY):
                steps.append((people.ENTITY, step[len(people.ENTITY):], None))
                continue
            person = step.startswith("person:")
            view, key = step.split(":", 2)[1:] if person else step.partition(":")[::2]
            steps.append((person, view, search.row(conn, view, key)))
        tv = trows = None
        hidden = 0
        if boxes.table:                                # ruling 92 (5): the register's table, kept while a search runs
            tv = cat.BY_NAME[boxes.table]
            tv = tv if tv.name in held else panes.main_view(tv.register, held)
            if tv is not None:
                total, trows, hidden = search.table(conn, tv, boxes.upto, boxes.removed)
        # ruling 111: the results list entities, so only the path's panes and the table cite a document or name a far row
        cited = [r.get("document") for k, _, r in steps if r and k != people.ENTITY]
        docs = document.statuses(conn, cited)          # ruling 86 (4): one query for every "source" link on the page
        shown_rows = [(cat.BY_NAME[view], r) for k, view, r in steps if r and k != people.ENTITY] + [(tv, r) for r in trows or ()]
        far = search.far_rows(conn, shown_rows, held)  # ruling 92 (2): one query per far view for every key shown
        listed = [(v, r) for hits in results.values() if isinstance(hits, list) for v, _, rows in hits for r in rows
                  if v.kind == "organisation" and not panes.is_suppressed(v, r)]
        related = lineage.related_refs(conn, [links_view.ref(v, r["key"]) for v, r in listed])     # ruling 106 (2): the word
        for v, r in listed:
            if links_view.ref(v, r["key"]) in related:
                r["_related"] = related[links_view.ref(v, r["key"])]
        out = [panes.left_pane(q, search.held_registers(held), boxes)]
        if near_names:
            out.append(panes.near_names_pane(q, near.near_names(conn, q, asked, registers=regs, held=held), boxes))
        ents = None
        if asking:                                     # ruling 111: the results pane lists entities alone, in either state
            hits = [(v, r) for hits in results.values() if isinstance(hits, list) for v, _, rows in hits for r in rows]
            hits += [vr for c in (nearby or {}).values() if isinstance(c, dict) for vr in c.get("rows") or ()]
            ents = people.gather(conn, hits, people.named_groups(conn, q, asked, regs))     # ruling 108 (3): entity search
        chosen = dossier.parse(chosen)
        dos, centre = dossier_of(conn, chosen, q, boxes)
        if q or asked or tv is None or graph_open:    # with a table open and nothing asked, the table sits beside the search
            pane = panes.results_pane(q, results, held, regs, boxes, words, nearby, ents=ents,
                                      fold=collapse.folder(conn, boxes.collapse))     # ruling 112: a display choice, read only
            if asking or graph_open:                   # ruling 108 (4); ruling 110: the dossier under the graph
                g = graph.build(conn, q if regs else "", regs=regs, centre=centre, fields=asked if regs else None,
                                removed=boxes.removed, people=boxes.people, collapse=boxes.collapse) if graph_open else None
                side = graph.side_pane(boxes, centre, g, q, regs, chosen)
                out.append(f'<div class="duo">{pane}<div class="sidecol">{side}{dos}</div></div>')
            else:
                out.append(pane)
                if chosen:
                    out.append(dos)
        elif chosen:
            out.append(dos)
        if tv is not None:
            out.append(panes.table_pane(q, tv, total, trows, boxes._replace(table=tv.name), held, far, hidden))
        for i, (person, view, r) in enumerate(steps):
            so_far = path[:i + 1]
            if person == people.ENTITY:
                out.append(panes.entity_pane(entity_context(conn, view), q, so_far, boxes))
                continue
            v = cat.BY_NAME[view]
            if person:
                if r is None:
                    out.append('<section class="pane"><p class="why">row not found in the published view</p></section>')
                    continue
                out.append(panes.person_pane(person_context(conn, v, r, q, so_far, same, boxes)))
            else:
                if r is None:
                    out.append(f'<section class="pane"><div class="reg">{panes.esc(view)}</div>'
                               '<p class="why">row not found in the published view: its key has moved or it was withdrawn</p></section>')
                    continue
                out.append(panes.row_pane(row_context(conn, v, r, q, so_far, pinned, same, boxes, docs, far)))
        return panes.page(q, path, out, message, boxes, db=counter())


def render_graph(q: str, centre: str = "", conn=None, boxes: search.Boxes = search.FIRST, chosen: str = "", read=None) -> str:
    """What the graph tab's old address opens (ruling 111): the search page
    with the graph beside the results drawn now, centred on `centre` (`c=`)
    with its dossier under it, else the whole search. `read`, the check's
    session-reader connection (else `conn`, else one opened)."""
    return render(q, [], conn=read if read is not None else conn, boxes=boxes, chosen=chosen or centre, graph_open=True)


def graph_redirect(qs: dict) -> str:
    """The address the graph tab's old address answers with (ruling 111):
    `/graph?q=&…&c=&d=` and `/?tab=graph…`, as saved before the tab left the
    bar, become the search page on the same query, check boxes and state
    (`g=entities`), the graph open beside the results (`gv=1`), centred on
    `d`, else `c`, whose dossier opens under it."""
    q = (qs.get("q") or [""])[0].strip()[:200]
    d = dossier.parse((qs.get("d") or [""])[0]) or parse_centre((qs.get("c") or [""])[0])
    return panes.graph_open_href(q, search.boxes_of(qs), d)


def graph_answer(q: str, centre: str = "", conn=None, boxes: search.Boxes = search.FIRST, opened: str = "") -> dict:
    """GET /graph.json (ruling 100): the graph tab's graph as data, from the
    same `graph.build` on the product reader (pub only); the canvas asks it
    with `c`, one row's one hop, as the reader taps; `opened`, a group id,
    answers that entity's rows and their own links (ruling 105)."""
    with RENDER_LOCK, (contextlib.nullcontext(conn) if conn is not None else db.scan_connect()) as conn:
        held = db.pub_views(conn)
        regs = search.selection(boxes, search.held_registers(held))
        if opened:
            return graph.opened(people.entity(conn, opened), q, boxes)
        g = graph.build(conn, q if regs else "", regs=regs, centre=centre, fields=boxes.asked() if regs else None,
                        removed=boxes.removed, people=boxes.people, collapse=boxes.collapse)
        return graph.answer(g, q, boxes)


def render_uses(repo: str = uses.REPO, held: set = None, host: str = "", env=None, answer=None) -> str:
    """The use cases tab (ruling 87): the plan's table from `repo`, the copy
    the board runs from, read now; held views from `pub` on the product
    reader unless given (the test gives its own, and `answer` for the
    counter). `host`, the request's Host header, and `env` place the links
    to each use case's interface (ruling 89, uses.bases)."""
    if held is None:
        with RENDER_LOCK, db.scan_connect() as conn:
            held, answer = db.pub_views(conn), counter(conn)
    table = uses.read_text(uses.TABLE, repo)
    if table is None:
        return panes.page("", [], [panes.uses_pane([], missing=uses.TABLE)], tab="uses", db=answer)
    rows = uses.rows(table, uses.read_text(uses.NOT_HELD, repo), uses.read_templates(repo), held, uses.bases(host, env))
    return panes.page("", [], [panes.uses_pane(rows, source=uses.TABLE)], tab="uses", db=answer)


def render_list(which: str) -> str:
    with RENDER_LOCK, db.read_connect() as conn:
        if which == "pinned":
            return panes.page("", [], [panes.pins_pane(state.pins(conn))], db=counter())
        return panes.page("", [], [panes.paths_pane(state.paths(conn))], db=counter())


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "qv4-board/1"

    def log_message(self, fmt, *args):      # one line per request, no query text (a search is a person's typing)
        sys.stderr.write(f"{self.address_string()} {self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}\n")

    def send_html(self, body: str, status: int = 200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", POLICY)
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, data: bytes, ctype: str, cache: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def send_document(self, sha: str):
        """GET /doc/<sha256> (ruling 86 (4)): the captured bytes, read only, or
        a plain refusal; nothing else under /doc answers, so the store is never listed."""
        with RENDER_LOCK, db.read_connect() as conn:
            status, ctype, body = document.fetch(conn, sha)
        data = body if isinstance(body, bytes) else (body + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, x in document.HEADERS:
            self.send_header(k, x)
        if status == 200:
            self.send_header("Content-Disposition", f'inline; filename="{sha}"')
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, where: str):
        self.send_response(303)
        self.send_header("Location", where)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        qs = urllib.parse.parse_qs(url.query)
        try:
            if url.path == "/health":
                body = f"ok {self.server.server_address[1]}\n".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if url.path == "/uses":
                self.send_html(render_uses(host=self.headers.get("Host") or ""))
                return
            if url.path in ("/pinned", "/saved"):
                self.send_html(render_list(url.path[1:]))
                return
            if url.path.startswith("/static/"):
                found = assets.read(url.path[len("/static/"):])
                if found is None:
                    self.send_bytes(b"not here\n", "text/plain; charset=utf-8", "no-store", 404)
                else:
                    self.send_bytes(found[0], found[1], assets.CACHE)
                return
            if url.path.startswith("/doc/") or url.path == "/doc":
                self.send_document(url.path[len("/doc/"):])
                return
            if url.path not in ("/", "/graph", "/graph.json", "/dossier"):
                self.send_html("<p>not here</p>", 404)
                return
            q = (qs.get("q") or [""])[0].strip()[:200]
            boxes = search.boxes_of(qs)
            if url.path == "/graph.json":
                body = graph.to_json(graph_answer(q, parse_centre((qs.get("c") or [""])[0]), boxes=boxes,
                                                  opened=(qs.get("open") or [""])[0][:300])).encode("utf-8")
                self.send_bytes(body, "application/json; charset=utf-8", "no-store")
                return
            chosen = (qs.get("d") or [""])[0]
            if url.path == "/dossier":
                self.send_html(render_dossier(chosen, q, boxes=boxes))
                return
            if url.path == "/graph" or (qs.get("tab") or [""])[0] == "graph":     # ruling 111: the tab left the bar
                self.redirect(graph_redirect(qs))
                return
            path = parse_path((qs.get("p") or [""])[0])
            self.send_html(render(q, path, (qs.get("m") or [""])[0][:100], boxes=boxes, near_names="1" in (qs.get("near") or []),
                                  chosen=chosen, graph_open="1" in (qs.get(panes.GRAPH_OPEN) or [])))
        except Exception as exc:          # the page says what failed; the server stays up
            self.send_html(f"<p>the board could not answer: {panes.esc(type(exc).__name__)}: {panes.esc(exc)}</p>", 500)

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        form = urllib.parse.parse_qs(self.rfile.read(min(length, 65536)).decode("utf-8", "replace"))
        get = lambda k: (form.get(k) or [""])[0]
        try:
            q, path = get("q").strip()[:200], parse_path(get("p"))
            boxes = search.boxes_of(form)
            if url.path == "/pin":
                view, key = get("view"), get("key")
                if view in cat.BY_NAME and key:
                    state.pin(view, key, get("title"))
                    self.redirect(panes.href(q, path, boxes) + "&m=pinned")
                    return
            if url.path == "/save":
                if path:
                    state.save_path(get("name").strip(), q, path)
                    self.redirect(panes.href(q, path, boxes) + "&m=path+saved")
                    return
            self.send_html("<p>nothing to do</p>", 400)
        except Exception as exc:
            self.send_html(f"<p>the board could not write: {panes.esc(type(exc).__name__)}: {panes.esc(exc)}</p>", 500)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(bind: str = BIND, port: int = PORT):
    with Server((bind, port), Handler) as httpd:
        sys.stderr.write(f"qv4-board: listening on {bind}:{port} (the local network only)\n")
        httpd.serve_forever()
