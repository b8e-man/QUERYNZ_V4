"""See a version folder, on the local network only (hard limit 13), on a
port that is never the frozen product's 8300 or 8301 (plan 4.4). The
standard library's HTTP server; it serves the folder's files as they are
and renders three plain pages from them so a reader can look without a
JSON viewer: the index (`/`), a party (`/party/<file>`), a donor
(`/donor/<file>`). Nothing is written.

    python -m products.published_site preview [--version STAMP] [--port N] [--bind ADDR]
"""
from __future__ import annotations

import html
import http.server
import json
import os
import socketserver
import sys
import urllib.parse

from products.published_site import paths, version

PORT = int(os.environ.get("QV4_SITE_PORT") or 8430)
BIND = os.environ.get("QV4_SITE_BIND") or "0.0.0.0"
FORBIDDEN_PORTS = (8300, 8301)


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def money(x) -> str:
    return "—" if x is None else f"${float(x):,.2f}"


def check_port(port: int) -> None:
    if int(port) in FORBIDDEN_PORTS:
        raise ValueError(f"port {port} is the frozen product's; the preview never listens there (plan 4.4)")


def load(root: str, rel: str):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


def page(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(title)}</title>"
            "<style>body{font:15px/1.4 system-ui,sans-serif;margin:2em;max-width:70em}table{border-collapse:collapse}"
            "td,th{border-bottom:1px solid #ddd;padding:.2em .6em;text-align:left}td.n{text-align:right}small{color:#555}</style>"
            f"</head><body><h1>{esc(title)}</h1>{body}</body></html>")


def index_html(root: str) -> str:
    m = version.manifest_of(root)
    h = load(root, paths.path("home"))
    rows = "".join(f"<tr><td><a href='/party/{esc(os.path.basename(paths.path('subject', 'party', c['party'])))}'>{esc(c['party'])}</a>"
                   f"{' <small>front page</small>' if c['headline'] else ''}</td><td class='n'>{money(c['total_window'])}</td>"
                   f"<td class='n'>{money(c['named_window'])}</td><td class='n'>{esc(c['seats']['total'])}</td></tr>" for c in h["parties"])
    kinds = "".join(f"<li>{esc(k)}: {n}</li>" for k, n in sorted(m.get("written", {}).items()))
    nb = "".join(f"<li>{esc(k)}: {esc(v)}</li>" for k, v in sorted((m.get("kinds_not_built") or {}).items()))
    donors = "".join(f"<tr><td><a href='/donor/{esc(os.path.basename(d['page']))}'>{esc(d['name'])}</a> <small>{esc(d['kind'])}</small></td>"
                     f"<td class='n'>{money(d['total'])}</td></tr>" for d in h["donors"])
    body = (f"<p>Version <b>{esc(m['stamp'])}</b>, built from the frozen release listing <b>{esc(m.get('listing', {}).get('version'))}</b> "
            f"({esc(m.get('listing', {}).get('files'))} captured files). Template {esc(m.get('template'))} v{esc(m.get('template_version'))}. "
            f"Window from {esc(h['window_from'])}. This is a preview on the local network; nothing here is deployed.</p>"
            f"<h2>Parties</h2><table><tr><th>Party</th><th>Declared, window</th><th>Named (Part A)</th><th>Seats</th></tr>{rows}</table>"
            f"<h2>Largest donors</h2><table>{donors}</table>"
            f"<h2>Files written</h2><ul>{kinds}</ul>" + (f"<h2>Not built yet</h2><ul>{nb}</ul>" if nb else "")
            + f"<p><small>{esc(h['known_limits'])}</small></p><p><a href='/data/home.json'>home.json</a> · <a href='/SNAPSHOT.json'>manifest</a></p>")
    return page("Follow the Money, rebuilt: preview", body)


def party_html(root: str, name: str) -> str:
    p = load(root, f"data/subject/party/{name}")
    c = p.get("card") or p
    w = c["window"]
    yrs = "".join(f"<tr><td>{d['year']}</td><td class='n'>{money(d['total'])}</td><td class='n'>{money(n['total'])}</td>"
                  f"<td class='n'>{money(x['total'])}{' <small>sighted</small>' if x['covered_by_return'] else ''}</td>"
                  f"<td><small>{esc(d['basis'])}</small></td><td><small>{' '.join(esc(doc['document'][:12]) for doc in d['documents'])}</small></td></tr>"
                  for d, n, x in zip(w["series"], w["named_series"], w["disclosed_series"]))
    races = "".join(f"<li>{r}: declared {money(v['total'])}, named {money(v['named'])} ({v['named_rows']} rows), over the line {money(v['over_line'])}</li>"
                    for r, v in c["races"].items())
    body = (f"<p><a href='/'>← preview index</a></p><p>Window total <b>{money(w['total'])}</b>; named {money(w['named'])}; over ${w['line']:,} {money(w['over_line'])}. "
            f"Seats {esc(c['seats']['total'])}. {esc(w['basis'])}</p><ul>{races}</ul>"
            f"<table><tr><th>Year</th><th>Declared</th><th>Named</th><th>Disclosed</th><th>Basis</th><th>Document</th></tr>{yrs}</table>")
    return page(c["party"], body)


def donor_html(root: str, name: str) -> str:
    d = load(root, f"data/donor/{name}")
    rows = "".join(f"<tr><td>{r['year']}</td><td>{esc(r['party_name'])}</td><td class='n'>{money(r['amount'])}</td><td>{esc(r['source'])}"
                   f"{'' if r['counts'] else ' <small>sighted, not added</small>'}</td><td><small>{esc(r['document'][:12])} p{esc(r.get('page'))}</small></td></tr>"
                   for r in d["history"])
    t = d["totals"]
    body = (f"<p><a href='/'>← preview index</a></p><p>Total that counts <b>{money(t['total'])}</b>: returns {money(t['returns'])}, open-year disclosures "
            f"{money(t['open_year_disclosures'])}; sighted beside a return {money(t['disclosures_sighted'])}. Spellings: {esc(', '.join(d['identity']['spellings']))}.</p>"
            f"<table><tr><th>Year</th><th>Party</th><th>Amount</th><th>Source</th><th>Document</th></tr>{rows}</table><p><small>{esc(t['basis'])}</small></p>")
    return page(d["name"], body)


def make_handler(root: str):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)

        def log_message(self, fmt, *args):
            sys.stderr.write("qv4-site-preview: " + fmt % args + "\n")

        def send_html(self, text: str, status: int = 200):
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            try:
                if url.path in ("", "/"):
                    return self.send_html(index_html(root))
                if url.path.startswith("/party/"):
                    return self.send_html(party_html(root, os.path.basename(url.path)))
                if url.path.startswith("/donor/"):
                    return self.send_html(donor_html(root, os.path.basename(url.path)))
                if url.path == "/health":
                    return self.send_html("ok")
            except (OSError, ValueError, KeyError) as exc:
                return self.send_html(f"<p>not in this version: {esc(type(exc).__name__)}: {esc(exc)}</p>", 404)
            return super().do_GET()
    return Handler


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(root: str, bind: str = BIND, port: int = PORT):
    check_port(port)
    if not os.path.isfile(os.path.join(root, version.MANIFEST)):
        raise FileNotFoundError(f"{root} is not a version folder (no {version.MANIFEST})")
    with Server((bind, int(port)), make_handler(root)) as httpd:
        sys.stderr.write(f"qv4-site-preview: {root} on http://{bind}:{port}/ (the local network only; nothing deployed)\n")
        httpd.serve_forever()
