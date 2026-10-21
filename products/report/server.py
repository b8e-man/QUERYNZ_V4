"""The report's page, served on the local network only (design rule 7; hard
limit 13), with the least machinery that works: the standard library's HTTP
server, one page per request, no script. Routes:

  GET  /                         the form: a ref and a template
  GET  /report/<register>:<key>  the memo: the stable address of a report on a row, the ref as the board names it
                                 (?template=&format=html|text|json as below; contract.report_url builds it)
  GET  /report?ref=&template=&format=html|text|json     the memo, the query form the page's own form uses
                                 (&since=YYYY-MM-DD on either: rows dated on or after it are marked new)
  GET  /saved                    the saved memos      GET /saved/<id>   one saved memo, as text
  POST /save                     save the memo the page shows (ref, template, note)
  GET  /health                   'ok' and the port
  GET  /templates                the templates on disk, one line each

Reads of pub run on the product reader; the document's names are not read
here (the citation carries the hash). One page at a time, as the board does."""
from __future__ import annotations

import http.server
import json
import os
import socketserver
import sys
import threading
import urllib.parse

from products.report import build, db, memo, state, template as tpl

PORT = int(os.environ.get("QV4_REPORT_PORT") or 8440)
BIND = os.environ.get("QV4_REPORT_BIND") or "0.0.0.0"   # the local network; never a public address (hard limit 13)
BOARD_URL = os.environ.get("QV4_BOARD_URL") or ""
RENDER_LOCK = threading.Lock()
MAX_REF = 300


def templates() -> list:
    return sorted(tpl.folders())


def build_report(ref: str, template_name: str, conn=None, since: str = "") -> dict:
    t = tpl.by_name(template_name)
    if conn is not None:
        return build.build(conn, ref, t, since=since or None)
    with RENDER_LOCK, db.scan_connect() as c:
        return build.build(c, ref, t, since=since or None)


def render(ref: str, template_name: str = "subject", fmt: str = "html", message: str = "", saved: bool = False, conn=None, since: str = "") -> tuple:
    """(content type, body). `since`: a date (YYYY-MM-DD); rows dated on or
    after it are marked new."""
    if not ref:
        body = memo.page("<p class=\"note\">Name a row as the board names it: <code>register:key</code>, for example "
                         "<code>companies:companies/9429037782269</code> or a <code>party_returns:…/A/3</code> donor row. "
                         "Choose a template. The memo lists confirmed connections first, near ones beside them with their reasons, "
                         "cites every line, and says what it did not find and what is not held.</p>", "", template_name, templates(), message,
                         board_url=BOARD_URL)
        return "text/html; charset=utf-8", body
    report = build_report(ref, template_name, conn, since)
    if fmt == "text":
        return "text/plain; charset=utf-8", memo.text(report)
    if fmt == "json":
        return "application/json", json.dumps(build.public(report), default=state._json, indent=1)
    return "text/html; charset=utf-8", memo.page(memo.html_body(report), ref, template_name, templates(), message, saved, BOARD_URL)


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "qv4-report/1"

    def log_message(self, fmt, *args):      # one line per request, no query text
        sys.stderr.write(f"{self.address_string()} {self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}\n")

    def send(self, body: str, ctype: str = "text/html; charset=utf-8", status: int = 200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
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
            if url.path == "/templates":
                self.send("\n".join(templates()) + "\n", "text/plain; charset=utf-8")
                return
            if url.path == "/saved":
                with RENDER_LOCK, db.read_connect() as conn:
                    rows_ = state.saved(conn)
                items = "".join(f'<li><a href="/saved/{r["report_id"]}">{memo.esc(r["title"])}</a> <span class="meta">{memo.esc(r["ref"])} · '
                                f'{memo.esc(r["template"])} {memo.esc(r["version"])} · as of {memo.esc(r["as_of"])} · {memo.esc(r["made_at"])}'
                                f'{" · " + memo.esc(r["note"]) if r.get("note") else ""}{" · REFUSED" if r.get("problems") else ""}</span></li>' for r in rows_)
                self.send(memo.page(f"<h2>Saved memos</h2><ul>{items or '<li>none yet</li>'}</ul>", "", "subject", templates(), board_url=BOARD_URL))
                return
            if url.path.startswith("/saved/"):
                try:
                    report_id = int(url.path.split("/")[2])
                except (IndexError, ValueError):
                    self.send("<p>not here</p>", status=404)
                    return
                with RENDER_LOCK, db.read_connect() as conn:
                    r = state.one(conn, report_id)
                if not r:
                    self.send("<p>not here</p>", status=404)
                    return
                self.send(r["memo"], "text/plain; charset=utf-8")
                return
            if url.path == "/":
                ctype, body = render("", get("template", "subject"), message=get("m")[:100])
                self.send(body, ctype)
                return
            if url.path == "/report" or url.path.startswith("/report/"):
                ref = (urllib.parse.unquote(url.path[len("/report/"):]) if url.path.startswith("/report/") else get("ref"))[:MAX_REF]
                ctype, body = render(ref, get("template", "subject"), get("format", "html"), get("m")[:100], get("saved") == "1", since=get("since")[:10])
                self.send(body, ctype)
                return
            self.send("<p>not here</p>", status=404)
        except KeyError as exc:
            self.send(f"<p>the report could not answer: {memo.esc(exc)}</p>", status=404)
        except Exception as exc:          # the page says what failed; the server stays up
            self.send(f"<p>the report could not answer: {memo.esc(type(exc).__name__)}: {memo.esc(exc)}</p>", status=500)

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        form = urllib.parse.parse_qs(self.rfile.read(min(length, 65536)).decode("utf-8", "replace"))
        get = lambda k: (form.get(k) or [""])[0].strip()
        try:
            if url.path == "/save":
                ref, template_name, note = get("ref")[:MAX_REF], get("template") or "subject", get("note")
                if not ref:
                    self.send("<p>nothing to save</p>", status=400)
                    return
                report = build_report(ref, template_name)
                state.save(report, memo.text(report), note)
                self.send_response(303)
                self.send_header("Location", "/report?" + urllib.parse.urlencode({"ref": ref, "template": template_name, "saved": "1", "m": "memo saved"}))
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send("<p>nothing to do</p>", status=400)
        except Exception as exc:
            self.send(f"<p>the report could not write: {memo.esc(type(exc).__name__)}: {memo.esc(exc)}</p>", status=500)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(bind: str = BIND, port: int = PORT):
    with Server((bind, port), Handler) as httpd:
        sys.stderr.write(f"qv4-report: listening on {bind}:{port} (the local network only)\n")
        httpd.serve_forever()
