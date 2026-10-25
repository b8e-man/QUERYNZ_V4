"""The board's page, served on the local network only (design rule 7;
hard limit 13), with the least machinery that works: the standard
library's HTTP server, one page per request, no script. Routes:

  GET  /?q=<term>&p=<view:key|view:key|person:view:key…>&all=<0|1>&r=<register>…&first=&middle=&last=&address=&org=&year=
                    the search tab: the left pane (check boxes, the search box, the fields of the expanded search,
                    ruling 82), the results beside it with the near matches below them (ruling 83), then one pane per
                    step of the path
  GET  /graph?q=<term>&all=<0|1>&r=<register>…&c=<view:key>   the graph tab: the matching rows as nodes, the
                    connections their registers assert as edges, one hop; `c` re-centres on one row
  GET  /pinned      the pinned panes       GET /saved     the saved paths
  POST /pin         pin a pane             POST /save     save the path walked
  GET  /health      'ok' and the port, for the launcher

The read connection is opened per request and closed after; the two writes
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
from products.board import catalogue as cat
from products.board import db, graph, links_view, near, panes, search, state

PORT = int(os.environ.get("QV4_BOARD_PORT") or 8420)
BIND = os.environ.get("QV4_BOARD_BIND") or "0.0.0.0"   # the local network; never a public address (hard limit 13)
REPORT_URL = os.environ.get("QV4_REPORT_URL") or ""    # the subject report's server; unset, no pane offers a report
MAX_PANES = 12
RENDER_LOCK = threading.Lock()      # one page at a time: the session reader's cap is five connections, shared


def parse_path(p: str) -> list:
    steps = []
    for s in (p or "").split("|"):
        s = s.strip()
        if not s:
            continue
        if s.startswith("person:"):
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


def row_context(conn, v: cat.View, r: dict, q: str, path: list, pinned: set, same=None, boxes=None) -> dict:
    same = same or same_name_memo(conn)
    ref = links_view.ref(v, r["key"])
    same_words = search.names_of_row(v, r)
    ctx = {"v": v, "row": r, "q": q, "path": path, "pinned": (v.name, r["key"]) in pinned,
           "parent": search.parent(conn, v, r), "children": search.children(conn, v, r),
           "doc_names": docstore.names_of(r["document"], conn) if r.get("document") else [],
           "links": links_view.links_of(conn, ref), "group": links_view.group_of(conn, ref) if v.kind == "person" else {},
           "same": same(v, r), "same_words": same_words, "resolve": resolver(conn),
           "report": panes.report_href(REPORT_URL, ref), "boxes": boxes}
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


def render(q: str, path: list, message: str = "", conn=None, boxes: search.Boxes = search.FIRST) -> str:
    """The search tab. `conn` is a session-reader connection to reuse (the
    check passes its own); without one a connection is opened and closed.
    `boxes`: the form's check boxes, carried on every href (ruling 81)."""
    with RENDER_LOCK, (contextlib.nullcontext(conn) if conn is not None else db.read_connect()) as conn:
        held = db.pub_views(conn)
        regs = search.selection(boxes, search.held_registers(held))
        asked = boxes.asked()
        asking = bool(q or asked) and bool(regs)
        results = search.search(conn, q, limit=search.RESULTS_LIMIT, registers=regs, fields=asked) if asking else {}
        nearby = near.near(conn, q, asked, registers=regs, held=held) if asking else None     # ruling 83, below the exact results
        pinned = {(p["view"], p["key"]) for p in state.pins(conn)}
        same = same_name_memo(conn)
        words = panes.search_words(q, boxes)
        out = [panes.left_pane(q, search.held_registers(held), boxes),
               panes.results_pane(q, results, held, regs, boxes, words, nearby)]
        for i, step in enumerate(path):
            so_far = path[:i + 1]
            if step.startswith("person:"):
                _, view, key = step.split(":", 2)
                v = cat.BY_NAME[view]
                r = search.row(conn, view, key)
                if r is None:
                    out.append('<section class="pane"><p class="why">row not found in the published view</p></section>')
                    continue
                out.append(panes.person_pane(person_context(conn, v, r, q, so_far, same, boxes)))
            else:
                view, _, key = step.partition(":")
                v = cat.BY_NAME[view]
                r = search.row(conn, view, key)
                if r is None:
                    out.append(f'<section class="pane"><div class="reg">{panes.esc(view)}</div>'
                               '<p class="why">row not found in the published view: its key has moved or it was withdrawn</p></section>')
                    continue
                out.append(panes.row_pane(row_context(conn, v, r, q, so_far, pinned, same, boxes)))
        return panes.page(q, path, out, message, boxes)


def render_graph(q: str, centre: str = "", conn=None, boxes: search.Boxes = search.FIRST) -> str:
    """The graph tab, on the product reader (pub only); the check passes its own connection."""
    with RENDER_LOCK, (contextlib.nullcontext(conn) if conn is not None else db.scan_connect()) as conn:
        held = db.pub_views(conn)
        regs = search.selection(boxes, search.held_registers(held))
        g = graph.build(conn, q if regs else "", regs=regs, centre=centre, fields=boxes.asked() if regs else None)
        out = [panes.left_pane(q, search.held_registers(held), boxes, action="/graph", title="Graph the connections"),
               graph.pane(g, q, boxes, regs)]
        return panes.page(q, [], out, "", boxes, tab="graph")


def render_list(which: str) -> str:
    with RENDER_LOCK, db.read_connect() as conn:
        if which == "pinned":
            return panes.page("", [], [panes.pins_pane(state.pins(conn))])
        return panes.page("", [], [panes.paths_pane(state.paths(conn))])


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
            if url.path in ("/pinned", "/saved"):
                self.send_html(render_list(url.path[1:]))
                return
            if url.path not in ("/", "/graph"):
                self.send_html("<p>not here</p>", 404)
                return
            q = (qs.get("q") or [""])[0].strip()[:200]
            boxes = search.boxes_of(qs)
            if url.path == "/graph":
                self.send_html(render_graph(q, parse_centre((qs.get("c") or [""])[0]), boxes=boxes))
                return
            path = parse_path((qs.get("p") or [""])[0])
            self.send_html(render(q, path, (qs.get("m") or [""])[0][:100], boxes=boxes))
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
