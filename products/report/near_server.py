"""The on-request hook for stage 2 (ruling 151): the page's second pass.

A finished first report offers one link, "follow the near links"; the
reader who follows it gets the same report with the near section added
(products.report.near). The first report is built exactly as the page
builds it, then the second pass runs on it, on the same connection and
under the page's one lock. Nothing here is reached until the server's
route is wired to it (docs/research/step-9-near-links.md, "Wiring"):

  GET /report/<register>:<key>?near=1   (and /report?ref=…&near=1)
      the report with stage 2; format=html|text|json as the page's own

The query name `near` is the page's own, never a template's parameter.
Reads of pub on the product reader, as the page's."""
from __future__ import annotations

import json
import urllib.parse

from products.report import build, contract, db, memo, near, state

QUERY_NAME = "near"
ASKED = "1"


def asked(qs: dict) -> bool:
    """True when the page's query asks for the second pass (`near=1`)."""
    return ((qs.get(QUERY_NAME) or [""])[0] or "").strip() == ASKED


def href(ref: str, template_name: str = "subject", since: str = "", params: dict | None = None, fmt: str = "") -> str:
    """The address of the report on `ref` with stage 2."""
    q = {"template": template_name, **({"since": since} if since else {}), **(params or {}), QUERY_NAME: ASKED, **({"format": fmt} if fmt else {})}
    return contract.report_url(ref) + "?" + urllib.parse.urlencode(q)


def offer(report: dict, template_name: str = "subject", since: str = "", params: dict | None = None) -> str:
    """The one line a finished first report carries, as HTML: the link to
    the second pass. Empty for a report not found or already stage 2."""
    if not report.get("found") or report.get("stage") == 2:
        return ""
    return (f'<p class="note"><a href="{memo.esc(href(report["ref"], template_name, since, params))}">follow the near links</a>: '
            "a second pass lists the rows joined to these records by a name and nothing that confirms it, each with its reason; "
            "never counted with the records above</p>")


def build_stage2(ref: str, template_name: str, conn=None, since: str = "", params: dict | None = None) -> dict:
    """The first report on `ref`, then the second pass on it."""
    from products.report import server
    if conn is not None:
        return near.stage2(conn, server.build_report(ref, template_name, conn, since, params))
    with server.RENDER_LOCK, db.scan_connect() as c:
        return near.stage2(c, server.build_report(ref, template_name, c, since, params))


def render(ref: str, template_name: str = "subject", fmt: str = "html", message: str = "", saved: bool = False, conn=None, since: str = "",
           params: dict | None = None) -> tuple:
    """(content type, body) for the report with stage 2, in the page's three
    formats; the memo's own printers print the near section with the rest."""
    from products.report import server
    report = build_stage2(ref, template_name, conn, since, params)
    if fmt == "text":
        return "text/plain; charset=utf-8", memo.text(report) + "\n" + near.summary(report)
    if fmt == "json":
        return "application/json", json.dumps(build.public(report), default=state._json, indent=1)
    return "text/html; charset=utf-8", memo.page(memo.html_body(report), ref, template_name, server.templates(), message, saved, server.BOARD_URL,
                                                 since=since, params=server.declared_params(template_name, params))
