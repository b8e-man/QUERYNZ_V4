"""The scan's page, served on the local network only (design rule 7; hard
limit 13), with the least machinery that works: the standard library's
HTTP server, one page per request, no script, one render at a time (the
connection-cap lesson). Routes:

  GET /                               every scan on disk, its latest run, stale or current
  GET /scan/<name>[?page=N&grade=G&run=ID]   the latest run's list, paged; a run by id
  GET /scan/<name>/answers.csv        the whole run, each line with its citations
  GET /scan/<name>/answers.json       the same, with the run's record and the citations list
  GET /scan/<name>/citations.csv      the numbered citations
  GET /stale                          which scans are stale
  GET /health                         'ok' and the port

Reads `pub` on the product reader (the stale check), the scan's own tables
on the session reader. Runs are started by the runner, never by the page."""
from __future__ import annotations

import http.server
import os
import socketserver
import sys
import threading
import urllib.parse

from products.scan import db, out, run as R, state, template as tpl

PORT = int(os.environ.get("QV4_SCAN_PORT") or 8450)
BIND = os.environ.get("QV4_SCAN_BIND") or "0.0.0.0"   # the local network; never a public address (hard limit 13)
RENDER_LOCK = threading.Lock()


def scans() -> list:
    return sorted(tpl.folders())


def stale_map() -> dict:
    with db.pub_connect() as pub, db.state_read_connect() as st:
        pub.autocommit = True
        return {x["scan"]: x for x in R.stale(pub, st)}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "qv4-scan/1"

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} {self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}\n")

    def send(self, body: str, ctype: str = "text/html; charset=utf-8", status: int = 200, filename: str = ""):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        qs = urllib.parse.parse_qs(url.query)
        get = lambda k, d="": (qs.get(k) or [d])[0].strip()
        try:
            if url.path == "/health":
                self.send(f"ok {self.server.server_address[1]}\n", "text/plain")
                return
            if url.path == "/":
                with RENDER_LOCK:
                    sm = stale_map()
                    with db.state_read_connect() as st:
                        entries = [{"name": n, "title": tpl.by_name(n).title, "run": state.latest(st, n), "stale": sm.get(n, {}).get("stale", [])} for n in scans()]
                self.send(out.page(out.index_html(entries), scans=scans()))
                return
            if url.path == "/stale":
                with RENDER_LOCK:
                    sm = stale_map()
                lines = [f"{n}: " + ("never run" if x["never_run"] else (f"stale: {', '.join(x['stale'])} loaded since run {x['run_id']}" if x["stale"] else f"current (run {x['run_id']})"))
                         for n, x in sorted(sm.items())]
                self.send("\n".join(lines) + "\n", "text/plain; charset=utf-8")
                return
            if url.path.startswith("/scan/"):
                parts = url.path.split("/")
                name = urllib.parse.unquote(parts[2])
                if name not in scans():
                    self.send("<p>no such scan</p>", status=404)
                    return
                t = tpl.by_name(name)
                want = parts[3] if len(parts) > 3 else ""
                run_id = int(get("run", "0") or 0) or None
                with RENDER_LOCK, db.state_read_connect() as st:
                    r = state.run(st, run_id) if run_id else state.latest(st, name)
                    if not r or r["scan"] != name:
                        self.send(out.page(f"<h2>{out.esc(t.title)}</h2><p>no finished run yet: <code>python -m products.scan run {out.esc(name)}</code></p>", scans=scans()))
                        return
                    if want == "answers.csv":
                        self.send(out.csv_text(t, state.all_lines(st, r["run_id"])), "text/csv; charset=utf-8", filename=f"{name}-run{r['run_id']}.csv")
                        return
                    if want == "citations.csv":
                        self.send(out.citations_csv(state.citations(st, r["run_id"])), "text/csv; charset=utf-8", filename=f"{name}-run{r['run_id']}-citations.csv")
                        return
                    if want == "answers.json":
                        self.send(out.json_text(t, r, state.all_lines(st, r["run_id"]), state.citations(st, r["run_id"])), "application/json",
                                  filename=f"{name}-run{r['run_id']}.json")
                        return
                    page_no = max(1, int(get("page", "1") or 1))
                    grade = get("grade") if get("grade") in ("confirmed", "near", "contested") else ""
                    lines, total = state.lines(st, r["run_id"], page_no, state.PAGE, grade or None)
                    cites = state.citations(st, r["run_id"], sorted({c for ln in lines for c in ln["cites"]})) if lines else []
                    sm = stale_map()
                self.send(out.page(out.scan_html(t, r, lines, total, page_no, state.PAGE, cites, sm.get(name, {}).get("stale", []), grade), t.title, scans()))
                return
            self.send("<p>not here</p>", status=404)
        except Exception as exc:
            self.send(f"<p>the scan could not answer: {out.esc(type(exc).__name__)}: {out.esc(exc)}</p>", status=500)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(bind: str = BIND, port: int = PORT):
    with Server((bind, port), Handler) as httpd:
        sys.stderr.write(f"qv4-scan: listening on {bind}:{port} (the local network only)\n")
        httpd.serve_forever()
