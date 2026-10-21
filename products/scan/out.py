"""The list out: as a table on a page (HTML, paged, no script), and as
files a reader can take away (answers.csv, answers.json, citations.csv),
each line carrying its citations: a number per step that indexes the
citations list, and the citation's text inline so a line read alone still
says where it came from. The page's header says what the scan asked, what
it read and under which licence, when each view was loaded, the trust
settings in force, how long the run took, how many lines of each grade,
and whether a view has loaded since (stale)."""
from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import os

from products.scan import lines as L, state, template as tpl

CSS = """
body{margin:0;font:14px/1.45 system-ui,sans-serif;color:#222;background:#f4f4f2}
header{display:flex;gap:1rem;align-items:center;padding:.5rem 1rem;background:#fff;border-bottom:1px solid #ddd}
header h1{font-size:15px;margin:0 1rem 0 0;font-weight:600}
header a{color:#246}
main{max-width:96rem;margin:1rem auto;background:#fff;border:1px solid #d8d8d4;border-radius:4px;padding:1.5rem 2rem}
h2{font-size:18px;margin:0 0 .25rem}
h3{font-size:13px;margin:1.5rem 0 .4rem;text-transform:uppercase;letter-spacing:.04em;color:#555;border-bottom:1px solid #eee}
.meta,.note{font-size:12px;color:#666}
.note{font-style:italic}
.warn{color:#8a3b00;font-weight:600}
.stale{color:#8a1010;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border-bottom:1px solid #eee;padding:.3rem .4rem;text-align:left;vertical-align:top}
th{background:#fafaf8;position:sticky;top:0}
td.grade{text-transform:uppercase;letter-spacing:.04em;font-size:11px;color:#666;white-space:nowrap}
td.grade.near{color:#8a5a00}td.grade.contested{color:#8a1010}
.dates{color:#555;display:block}
.cite{color:#246;white-space:nowrap}
.hub,.reason{display:block;color:#8a3b00}
.reason{color:#666}
.pages a{margin-right:.6rem}
ol.cites{font-size:12px;color:#444}
code{font-size:12px;word-break:break-all}
ul{margin:.25rem 0;padding-left:1.2rem}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _dt(x) -> str:
    if isinstance(x, (dt.date, dt.datetime)):
        return x.isoformat(timespec="seconds") if isinstance(x, dt.datetime) else x.isoformat()
    return str(x or "")


# ── files ───────────────────────────────────────────────────────────────────

def csv_header(t: tpl.Template) -> list:
    out = ["n", "grade", "reasons", "hubs", "cites"]
    for s in t.steps:
        out += [s.label, f"{s.label}_ref", f"{s.label}_dates", f"{s.label}_cite", f"{s.label}_citation"] + [f"{s.label}_{c}" for c in s.columns]
    return out


def csv_row(t: tpl.Template, ln: dict) -> list:
    out = [ln["n"], ln["grade"], " | ".join(ln["reasons"]), " | ".join(f"{h['step']}: {h['text']}" for h in ln["hubs"]), ";".join(str(c) for c in ln["cites"])]
    for s, st in zip(t.steps, ln["steps"]):
        out += [st["title"], st["ref"], st["dates"], st["cite"], st["cite_text"]] + [st["values"].get(c, "") for c in s.columns]
    return out


def csv_text(t: tpl.Template, lines_iter) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(csv_header(t))
    for ln in lines_iter:
        w.writerow(csv_row(t, ln))
    return buf.getvalue()


def citations_csv(citations: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["n", "view", "key", "register", "document", "page", "place", "url"])
    for c in citations:
        w.writerow([c["n"], c["view"], c["key"], c["register"], c.get("document") or "", c.get("page") if c.get("page") is not None else "",
                    c.get("place") or "", c.get("url") or ""])
    return buf.getvalue()


def run_doc(t: tpl.Template, r: dict) -> dict:
    return {"scan": r["scan"], "version": r["version"], "title": t.title, "question": r["question"], "join": t.join, "owner": t.owner,
            "run_id": r["run_id"], "started_at": _dt(r.get("started_at")), "finished_at": _dt(r.get("finished_at")),
            "seconds": float(r["seconds"]) if r.get("seconds") is not None else None, "lines": r.get("lines"), "limited": r.get("limited"),
            "starts": r.get("starts"), "settings": r.get("settings"), "views": r.get("views"), "grades": r.get("grades"), "hubs": r.get("hubs"),
            "problems": r.get("problems") or [], "note": r.get("note") or "",
            "reads": [{"view": x.view, "licence": x.licence, "attribution": x.attribution, "refresh": x.refresh} for x in t.reads],
            "limits": list(t.limits), "steps": [{"label": s.label, "view": s.view, "views": list(s.views), "by": s.by, "on": list(s.on), "rule": s.rule,
                                                  "number": list(s.number), "optional": s.optional, "namesakes": s.namesakes, "columns": list(s.columns)} for s in t.steps]}


def json_text(t: tpl.Template, r: dict, lines_iter, citations: list) -> str:
    doc = {"run": run_doc(t, r), "lines": list(lines_iter), "citations": citations}
    return json.dumps(doc, default=state._json, indent=1)


def export(t: tpl.Template, out_dir: str, run_id: int = None) -> list:
    """Writes answers.csv, answers.json and citations.csv for the run into out_dir; returns the paths."""
    os.makedirs(out_dir, exist_ok=True)
    with state.db.state_read_connect() as conn:
        r = state.run(conn, run_id) if run_id else state.latest(conn, t.name)
        if not r:
            raise KeyError(f"no finished run of {t.name}")
        cites = state.citations(conn, r["run_id"])
        paths = []
        for name, text in (("answers.csv", csv_text(t, state.all_lines(conn, r["run_id"]))),
                           ("answers.json", json_text(t, r, state.all_lines(conn, r["run_id"]), cites)),
                           ("citations.csv", citations_csv(cites))):
            p = os.path.join(out_dir, name)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            paths.append(p)
    return paths


# ── the page ────────────────────────────────────────────────────────────────

def page(body: str, title: str = "QueryNZ register scan", scans: list = (), message: str = "") -> str:
    links = " ".join(f'<a href="/scan/{esc(n)}">{esc(n)}</a>' for n in scans)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title><style>{CSS}</style></head>'
            f'<body><header><h1><a href="/">QueryNZ register scan</a></h1>{links} <a href="/stale">stale?</a>'
            f'{" <span class=note>" + esc(message) + "</span>" if message else ""}</header><main>{body}</main></body></html>')


def index_html(entries: list) -> str:
    rows = []
    for e in entries:
        r = e.get("run")
        if r:
            when = f'run {r["run_id"]}, {esc(_dt(r.get("finished_at")))}, {r.get("lines"):,} lines in {float(r.get("seconds") or 0):.1f} s'
        else:
            when = "never run"
        stale = ('<span class="stale">stale: ' + esc(", ".join(e["stale"])) + " loaded since</span>") if e.get("stale") and r else ""
        rows.append(f'<tr><td><a href="/scan/{esc(e["name"])}">{esc(e["name"])}</a></td><td>{esc(e["title"])}</td><td>{when} {stale}</td></tr>')
    return ("<h2>Scans</h2><p class=\"note\">Each scan asks one question of every row of a register or a join of registers and lists the "
            "answers with their dates, their citations and their grade. Nothing here says one fact caused another; an empty list says "
            "none found, never that none exists. Local network only.</p>"
            f'<table><tr><th>scan</th><th>question</th><th>latest run</th></tr>{"".join(rows)}</table>')


def _header_html(t: tpl.Template, r: dict, stale_views: list) -> str:
    s = r.get("settings") or {}
    views = "".join(f'<li>pub.{esc(v["view"])}: loaded {esc(v.get("loaded_at") or "not stated")}'
                    f'{" <span class=stale>loaded since: stale</span>" if v["view"] in stale_views else ""}</li>' for v in (r.get("views") or []))
    reads = "".join(f'<li>pub.{esc(x.view)}: {esc(x.licence)}{"; attribution: " + esc(x.attribution) if x.attribution else ""}'
                    f'{"; refresh: " + esc(x.refresh) if x.refresh else ""}</li>' for x in t.reads)
    limits = "".join(f"<li>{esc(x)}</li>" for x in t.limits)
    g = r.get("grades") or {}
    starts = "; ".join(f'pub.{esc(x["view"])}: {x["lines"]:,} lines in {x["seconds"]:.1f} s' for x in (r.get("starts") or []))
    problems = ("".join(f'<li class="warn">{esc(p)}</li>' for p in (r.get("problems") or [])))
    return (f"<h2>{esc(t.title)}</h2><p><b>Question.</b> {esc(t.question)}</p><p><b>Join.</b> {esc(t.join)}</p>"
            f'<p class="meta">Run {r["run_id"]}, {esc(_dt(r.get("started_at")))} to {esc(_dt(r.get("finished_at")))}: '
            f'{(r.get("lines") or 0):,} lines in {float(r.get("seconds") or 0):.1f} s ({esc(starts)}); '
            f'{g.get("confirmed", 0):,} confirmed, {g.get("near", 0):,} near, {g.get("contested", 0):,} contested; {r.get("hubs") or 0:,} lines with a hub flagged'
            f'{"; cut at " + str(r["limited"]) + " lines on purpose" if r.get("limited") else ""}.'
            f'{" " + esc(r["note"]) if r.get("note") else ""}</p>'
            f'<p class="meta">Trust settings in force: chains {esc(s.get("chains", {}).get("value"))} ({esc(s.get("chains", {}).get("status"))}); '
            f'through people {esc(s.get("through_people", {}).get("value"))} ({esc(s.get("through_people", {}).get("status"))}).</p>'
            f'<h3>Views read, and when each was loaded</h3><ul class="meta">{views}</ul>'
            f'<h3>Licences</h3><ul class="meta">{reads}</ul><h3>Known limits</h3><ul class="meta">{limits}</ul>'
            + (f'<h3>Refused: the presentation rules found problems</h3><ul>{problems}</ul>' if problems else ""))


def table_html(t: tpl.Template, lines: list, total: int, page_no: int, size: int, base: str, grade: str = "") -> str:
    head = "<tr><th>n</th><th>grade</th>" + "".join(f"<th>{esc(s.label)}</th>" for s in t.steps) + "<th>cites</th></tr>"
    rows = []
    for ln in lines:
        cells = []
        for s, st in zip(t.steps, ln["steps"]):
            if st.get("absent"):
                cells.append(f'<td class="note">{esc(st["title"])}</td>')
                continue
            vals = "".join(f'<span class="meta">{esc(c)}: {esc(x)}</span><br>' for c, x in (st.get("values") or {}).items())
            cells.append(f'<td>{esc(st["title"])} <span class="cite">[{st["cite"]}]</span><span class="dates">{esc(st["dates"])}</span>{vals}</td>')
        extra = "".join(f'<span class="reason">{esc(x)}</span>' for x in ln["reasons"]) + "".join(f'<span class="hub">hub, {esc(h["step"])}: {esc(h["text"])}</span>' for h in ln["hubs"])
        rows.append(f'<tr><td>{ln["n"]}</td><td class="grade {esc(ln["grade"])}">{esc(ln["grade"])}{extra}</td>{"".join(cells)}'
                    f'<td class="cite">{esc(";".join(str(c) for c in ln["cites"]))}</td></tr>')
    pages = max(1, (total + size - 1) // size)
    q = f"&grade={esc(grade)}" if grade else ""
    nav = " ".join(f'<a href="{base}?page={p}{q}">{p}</a>' if p != page_no else f"<b>{p}</b>"
                   for p in sorted({1, pages, *range(max(1, page_no - 3), min(pages, page_no + 3) + 1)}))
    filt = " ".join(f'<a href="{base}?page=1&grade={g}">{g}</a>' if g != grade else f"<b>{g}</b>" for g in L.GRADES) + f' <a href="{base}">all</a>'
    return (f'<h3>Answers: {total:,} lines{" graded " + esc(grade) if grade else ""}, page {page_no} of {pages}</h3>'
            f'<p class="pages">{nav} · show only: {filt} · take away: <a href="{base}/answers.csv">CSV</a> <a href="{base}/answers.json">JSON</a> '
            f'<a href="{base}/citations.csv">citations CSV</a></p>'
            f"<table>{head}{''.join(rows)}</table>" if total else
            f'<h3>Answers</h3><p>{esc(base and "")}none found in ' + esc(", ".join(sorted({x.view for x in t.reads}))) + "</p>")


def cites_html(citations: list) -> str:
    items = "".join(f'<li value="{c["n"]}"><code>{esc(L.cite_text(c))}</code></li>' for c in citations)
    return f'<h3>Citations on this page</h3><ol class="cites">{items}</ol>' if citations else ""


def scan_html(t: tpl.Template, r: dict, lines: list, total: int, page_no: int, size: int, citations: list, stale_views: list, grade: str = "") -> str:
    base = f"/scan/{t.name}"
    body = _header_html(t, r, stale_views)
    if r.get("problems"):
        body += "<p class=\"warn\">The list is not shown: the presentation rules refused this run.</p>"
    else:
        body += table_html(t, lines, total, page_no, size, base, grade) + cites_html(citations)
    return body
