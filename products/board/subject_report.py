"""The board's subject report tab (Arthur, 9 November 2026: "we need it to be a tab in the same interface design and we
need it to maintain state"). The subject report's own search, build and memo (products/report), drawn inside the
board's page under its bar, in the board's design; nothing of the report's server is asked.

One crossing of the one-way rule, named in tests/test_imports_one_way.py like the Papers Past tab's: this file alone
calls products.report, which reads only the published tables, as the report's own server does. The memo's own links
(a report from another row, `/report/<ref>?template=…`) are turned into this tab's addresses, so every step stays in the
tab; the tab's state is its address (the term, the row, the template, the since date), and the bar's script
(static/tabs.js) brings each tab back to the address it was last on.

    GET /subject-report?q=&ref=&template=&since=&c=1&c.<type>=on&c.<type>.<variable>=…

The connections pane (Arthur, 10 November 2026; ruling 159: on this tab only) opens beside a report: every connection
type the report listed or set aside, with its count, a tick to show it or not and a dropdown for each of its type's
variables (products/report/connections.toml). A change sends the pane's form (static/connections.js), and the report is
rebuilt with the setting, because a setting changes what is followed. The settings are in the address (`c.…`), so a
filtered report reopens as it was; with none the subject's base configuration applies. Only types, counts and
controls are in the pane: the report keeps its notes.
"""
from __future__ import annotations

import html
import re
import urllib.parse

from products.board import assets, panes
from products.report import build, connections, memo, search, template

PATH = "/subject-report"
TAB = "subject report"
DEFAULT_TEMPLATE = "diagnostic"
INTRO = ("Type a person, company or organisation name and choose a row: the report starts from it, with the template "
         "chosen beside the box. The diagnostic template reads every register that names someone and follows every link, "
         "each labelled with its rule; the others read what their use case names. Confirmed connections first, near ones "
         "beside them with their reasons; every line cited.")
_REPORT_HREF = re.compile(r'href="/report/([^"?]*)(?:\?([^"]*))?"')


def templates() -> list:
    return sorted(template.folders())


def chosen(name: str) -> str:
    return name if name in template.folders() else DEFAULT_TEMPLATE


def href(q: str = "", ref: str = "", template_name: str = DEFAULT_TEMPLATE, since: str = "") -> str:
    pairs = [(k, v) for k, v in (("q", q), ("ref", ref), ("template", "" if template_name == DEFAULT_TEMPLATE else template_name),
                                 ("since", since)) if v]
    return PATH + ("?" + urllib.parse.urlencode(pairs) if pairs else "")


def in_tab(body: str, template_name: str) -> str:
    """The memo's links to a report on another row, made this tab's: `/report/<ref>?template=x&since=y` becomes
    `/subject-report?ref=<ref>&template=x&since=y`; a link with no template keeps the one in use."""
    def one(m):
        ref = urllib.parse.unquote(m.group(1))
        rest = dict(urllib.parse.parse_qsl(html.unescape(m.group(2) or "")))
        return 'href="' + panes.esc(href("", ref, rest.pop("template", template_name), rest.pop("since", ""))) + '"'
    return _REPORT_HREF.sub(one, body)


def form(q: str, template_name: str, since: str) -> str:
    opts = "".join(f'<option value="{panes.esc(n)}"{" selected" if n == template_name else ""}>{panes.esc(n)}</option>'
                   for n in templates())
    return (f'<form method="get" action="{PATH}"><input type="search" name="q" value="{panes.esc(q)}" '
            'placeholder="a person, company or organisation name" aria-label="a person, company or organisation name" autofocus> '
            f'<label>template <select name="template" aria-label="template">{opts}</select></label> '
            f'<label title="rows dated on or after this day are marked new">since <input name="since" value="{panes.esc(since)}" '
            'placeholder="YYYY-MM-DD" size="10" aria-label="since"></label> <button>search</button></form>')


def pane(q: str, ref: str, template_name: str, since: str, body: str, failed: str = "") -> str:
    out = ['<section class="pane memo" id="subject-report">', f'<div class="reg">subject report · {panes.esc(template_name)}</div>',
           form(q, template_name, since)]
    if ref:
        back = href(q, "", template_name, since) if q else ""
        out.append('<div class="actions">' + (f'<a href="{panes.esc(back)}">back to the rows for “{panes.esc(q)}”</a> ' if back else "")
                   + f'<span class="meta">row {panes.esc(ref)}</span></div>')
    if failed:
        out.append(f'<p class="warn">the report could not answer: {panes.esc(failed)}</p>')
    out.append(body or f'<p class="note">{panes.esc(INTRO)}</p>')
    out.append("</section>")
    return "\n".join(out)


CONNECTIONS_CSS = (".pane.connections fieldset{border:0;border-top:1px solid #3a404c;margin:0;padding:.35rem 0}"
                   ".pane.connections .count{color:#aab1bc;font-size:12px;margin-left:.3rem}"
                   ".pane.connections .off{color:#6c7380}"
                   ".pane.connections select{color:#e8eaed;background:#232833;border:1px solid #5a6270;border-radius:3px;margin:.15rem .3rem 0 0}"
                   ".pane.connections .vars{display:flex;flex-wrap:wrap;gap:.1rem .4rem;font-size:12px;color:#aab1bc;margin-left:1.4rem}"
                   ".pane.memo .hubs{border:1px solid #ffb26b;border-radius:4px;padding:.25rem .6rem;margin:.5rem 0}"
                   ".pane.memo .hubs li.hub strong{color:#ffb26b;font-weight:normal}")


def query_settings(qs: dict) -> dict:
    """The pane's names from the page's query (`c` and `c.…`), each a short value; nothing else."""
    out = {}
    for k, v in (qs or {}).items():
        if k == connections.QUERY or k.startswith(connections.QUERY + "."):
            v = v[0] if isinstance(v, (list, tuple)) else v
            if len(k) <= 80:
                out[k] = str(v or "").strip()[:20]
    return out


def _count_text(r: dict) -> str:
    bits = [f"{r['listed']:,} listed"] if r["listed"] else []
    if r["set_aside"]:
        bits.append(f"{r['set_aside']:,} set aside")
    return " · ".join(bits) or "none"


def connections_pane(q: str, ref: str, template_name: str, since: str, report: dict) -> str:
    """The pane beside the report: types, counts and controls, and nothing else (Arthur: keep the notes out of it)."""
    con = report.get("connections") or {}
    hidden = [("q", q), ("ref", ref), ("template", template_name), ("since", since), (connections.QUERY, "1")]
    out = ['<section class="pane left connections" id="connections">', '<div class="reg">connections</div>',
           f'<form class="connections" method="get" action="{PATH}">']
    out += [f'<input type="hidden" name="{panes.esc(k)}" value="{panes.esc(v)}">' for k, v in hidden if v]
    if con.get("kind_words"):
        out.append(f'<p class="meta">base: {panes.esc(con["kind_words"])}</p>')
    for r in connections.pane_rows(report):
        name = f'{connections.QUERY}.{r["key"]}'
        out.append(f'<fieldset><label class="{"" if r["show"] else "off"}"><input type="checkbox" name="{panes.esc(name)}" value="on"'
                   f'{" checked" if r["show"] else ""}> {panes.esc(r["words"])}</label><span class="count">{panes.esc(_count_text(r))}</span>')
        if r["variables"]:
            out.append('<div class="vars">')
            for var, words, value, choices in r["variables"]:
                opts = "".join(f'<option value="{panes.esc(k)}"{" selected" if k == value else ""}>{panes.esc(w)}</option>' for k, w in choices)
                out.append(f'<label>{panes.esc(words)} <select name="{panes.esc(name + "." + var)}">{opts}</select></label>')
            out.append("</div>")
        out.append("</fieldset>")
    out.append(f'<div class="actions"><button>apply</button> <a href="{panes.esc(href(q, ref, template_name, since))}">base configuration</a></div>')
    out.append("</form>")
    out.append(f'<script src="{panes.esc(assets.url("connections.js"))}" defer></script>')
    out.append("</section>")
    return "\n".join(out)


def render(conn, q: str = "", ref: str = "", template_name: str = "", since: str = "", db=None, qs: dict | None = None) -> str:
    """The tab on `conn`, a reader connection: the start (the search box), the rows a name finds, or the memo on a row with
    the connections pane beside it; `qs`, the pane's settings from the address (`c.…`)."""
    template_name = chosen(template_name)
    body, failed, side = "", "", ""
    try:
        if ref:
            t = template.by_name(template_name)
            kind, settings = connections.settings_for(conn, ref, query_settings(qs))
            report = build.build(conn, ref, t, since=since or None, walker=connections.walker(settings, kind, stage=t.stage))
            side = connections_pane(q, ref, template_name, since, report) if report.get("found") else ""
            body = in_tab(memo.html_body(report), template_name)
            if q:   # the term travels on, so "back" and the memo's own links keep it
                body = body.replace(f'{PATH}?ref=', f'{PATH}?q={urllib.parse.quote(q)}&amp;ref=')
        elif q:
            body = in_tab(memo.search_results(q, search.search(conn, q), template_name, since), template_name)
            body = body.replace(f'{PATH}?ref=', f'{PATH}?q={urllib.parse.quote(q)}&amp;ref=')
    except Exception as exc:  # noqa: BLE001 — the pane says what failed
        conn.rollback()
        failed = f"{type(exc).__name__}: {exc}".splitlines()[0]
    style = f"<style>{CONNECTIONS_CSS}</style>"
    return panes.page("", [], [style] + ([side] if side else []) + [pane(q, ref, template_name, since, body, failed)], tab=TAB, db=db)
