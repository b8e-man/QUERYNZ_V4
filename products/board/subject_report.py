"""The board's subject report tab (Arthur, 9 November 2026: "we need it to be a tab in the same interface design and we
need it to maintain state"). The subject report's own search, build and memo (products/report), drawn inside the
board's page under its bar, in the board's design; nothing of the report's server is asked.

One crossing of the one-way rule, named in tests/test_imports_one_way.py like the Papers Past tab's: this file alone
calls products.report, which reads only the published tables, as the report's own server does. The memo's own links
(a report from another row, `/report/<ref>?template=…`) are turned into this tab's addresses, so every step stays in the
tab; the tab's state is its address (the term, the row, the template, the since date), and the bar's script
(static/tabs.js) brings each tab back to the address it was last on.

    GET /subject-report?q=&ref=&template=&since=
"""
from __future__ import annotations

import html
import re
import urllib.parse

from products.board import panes
from products.report import build, memo, search, template

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


def render(conn, q: str = "", ref: str = "", template_name: str = "", since: str = "", db=None) -> str:
    """The tab on `conn`, a reader connection: the start (the search box), the rows a name finds, or the memo on a row."""
    template_name = chosen(template_name)
    body, failed = "", ""
    try:
        if ref:
            report = build.build(conn, ref, template.by_name(template_name), since=since or None)
            body = in_tab(memo.html_body(report), template_name)
            if q:   # the term travels on, so "back" and the memo's own links keep it
                body = body.replace(f'{PATH}?ref=', f'{PATH}?q={urllib.parse.quote(q)}&amp;ref=')
        elif q:
            body = in_tab(memo.search_results(q, search.search(conn, q), template_name, since), template_name)
            body = body.replace(f'{PATH}?ref=', f'{PATH}?q={urllib.parse.quote(q)}&amp;ref=')
    except Exception as exc:  # noqa: BLE001 — the pane says what failed
        conn.rollback()
        failed = f"{type(exc).__name__}: {exc}".splitlines()[0]
    return panes.page("", [], [pane(q, ref, template_name, since, body, failed)], tab=TAB, db=db)
