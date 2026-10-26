"""The report's page, served on the local network only (design rule 7; hard
limit 13), with the least machinery that works: the standard library's HTTP
server, one page per request, no script. Routes:

  GET  /?q=&template=            the start page: a name search (a person, company or organisation), the rows it
                                 finds across the published views listed, each a link to the report on it (search.py)
  GET  /report/<register>:<key>  the memo: the stable address of a report on a row, the ref as the board names it
                                 (?template=&format=html|text|json as below; contract.report_url builds it)
  GET  /report?ref=&template=&format=html|text|json     the memo, the query form (the plain-text link uses it)
                                 (&since=YYYY-MM-DD on either: rows dated on or after it are marked new;
                                 &<name>=<value> for a parameter the template declares, which the form offers;
                                 one it does not declare is refused, 400)
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

from products.report import build, db, memo, search, state, template as tpl

PORT = int(os.environ.get("QV4_REPORT_PORT") or 8440)
BIND = os.environ.get("QV4_REPORT_BIND") or "0.0.0.0"   # the local network; never a public address (hard limit 13)
BOARD_URL = os.environ.get("QV4_BOARD_URL") or ""
RENDER_LOCK = threading.Lock()
MAX_REF = 300


def templates() -> list:
    return sorted(tpl.folders())


def build_report(ref: str, template_name: str, conn=None, since: str = "", params: dict | None = None) -> dict:
    t = tpl.by_name(template_name)
    if conn is not None:
        return build.build(conn, ref, t, since=since or None, params=params)
    with RENDER_LOCK, db.scan_connect() as c:
        return build.build(c, ref, t, since=since or None, params=params)


def declared_params(template_name: str, given: dict | None = None) -> list:
    """The parameters the template declares, for the form, with what the
    reader gave as the value shown; an undeclared name is not here (the
    builder refuses it)."""
    try:
        t = tpl.by_name(template_name)
    except KeyError:
        return []
    return [{"name": p.name, "kind": p.kind, "means": p.means, "default": p.default, "given": (given or {}).get(p.name, "")} for p in t.params]


def render(ref: str, template_name: str = "subject", fmt: str = "html", message: str = "", saved: bool = False, conn=None, since: str = "",
           params: dict | None = None, term: str = "") -> tuple:
    """(content type, body). With no ref, the start page: the name search,
    and with `term` the rows it finds, each a link to its report. `since`: a
    date (YYYY-MM-DD); rows dated on or after it are marked new. `params`: {name: value} for parameters the
    template declares; one it does not declare raises KeyError, which the
    page answers 400 and the command line prints."""
    if not ref:
        if term:
            if conn is not None:
                found = search.search(conn, term)
            else:
                with RENDER_LOCK, db.scan_connect() as c:
                    found = search.search(c, term)
            body = memo.search_results(term, found, template_name, since, declared_params(template_name, params))
        else:
            body = ("<p class=\"note\">Type a person, company or organisation name. The page lists the rows of the published registers "
                    "that carry it; choose one and the report starts from it, with the template chosen beside the box. "
                    "The memo lists confirmed connections first, near ones beside them with their reasons, cites every line, "
                    "and says what it did not find and what is not held.</p>")
        return "text/html; charset=utf-8", memo.page(body, "", template_name, templates(), message, board_url=BOARD_URL, since=since,
                                                     params=declared_params(template_name, params), term=term)
    report = build_report(ref, template_name, conn, since, params)
    if fmt == "text":
        return "text/plain; charset=utf-8", memo.text(report)
    if fmt == "json":
        return "application/json", json.dumps(build.public(report), default=state._json, indent=1)
    return "text/html; charset=utf-8", memo.page(memo.html_body(report), ref, template_name, templates(), message, saved, BOARD_URL,
                                                 since=since, params=declared_params(template_name, params))


QUERY_OWN = frozenset({"ref", "template", "format", "m", "saved", "since", "q"})   # the page's own query names; the rest are a template's parameters


def query_params(qs: dict) -> dict:
    return {k: (v or [""])[0].strip()[:100] for k, v in qs.items() if k not in QUERY_OWN and (v or [""])[0].strip()}


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
                ctype, body = render("", get("template", "subject"), message=get("m")[:100], since=get("since")[:10], params=query_params(qs),
                                     term=get("q")[:search.MAX_TERM])
                self.send(body, ctype)
                return
            if url.path == "/report" or url.path.startswith("/report/"):
                ref = (urllib.parse.unquote(url.path[len("/report/"):]) if url.path.startswith("/report/") else get("ref"))[:MAX_REF]
                try:
                    ctype, body = render(ref, get("template", "subject"), get("format", "html"), get("m")[:100], get("saved") == "1", since=get("since")[:10],
                                         params=query_params(qs))
                except KeyError as exc:
                    if "declares no parameter" not in str(exc):
                        raise
                    self.send(f"<p>refused: {memo.esc(exc.args[0] if exc.args else exc)}</p>", status=400)
                    return
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
                since = get("since")[:10]
                params = {k: get(k)[:100] for k in form if k not in ("ref", "template", "note", "since") and get(k)}
                report = build_report(ref, template_name, since=since, params=params)
                state.save(report, memo.text(report), note)
                self.send_response(303)
                self.send_header("Location", "/report?" + urllib.parse.urlencode({"ref": ref, "template": template_name, "saved": "1", "m": "memo saved",
                                                                                  **({"since": since} if since else {}), **params}))
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
