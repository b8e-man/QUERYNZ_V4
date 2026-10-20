"""The memo: the report printed, as plain text (for a file or a printer) and
as HTML with a print stylesheet (for the page). Answer first: the subject,
the group's standing and the flags that fired; then each section, confirmed
connections before near ones, every line with its dates and its citation
number; the hubs met; what the walk left out; what is not held; the
template's known limits; the numbered citations last. Pure: a report in, a
string out. Every value is escaped in the HTML."""
from __future__ import annotations

import html

from products.report import rows

GRADE_WORD = {"confirmed": "confirmed", "near": "near"}
CSS = """
body{margin:0;font:14px/1.45 system-ui,sans-serif;color:#222;background:#f4f4f2}
header{display:flex;gap:1rem;align-items:center;padding:.5rem 1rem;background:#fff;border-bottom:1px solid #ddd}
header h1{font-size:15px;margin:0 1rem 0 0;font-weight:600}
header input{padding:.3rem .5rem;font-size:14px}
header a{color:#246}
main{max-width:52rem;margin:1rem auto;background:#fff;border:1px solid #d8d8d4;border-radius:4px;padding:1.5rem 2rem}
h2{font-size:18px;margin:0 0 .25rem}
h3{font-size:13px;margin:1.5rem 0 .4rem;text-transform:uppercase;letter-spacing:.04em;color:#555;border-bottom:1px solid #eee}
.meta,.note,.why{font-size:12px;color:#666}
.note{font-style:italic}
.warn{color:#8a3b00;font-weight:600}
.red{color:#8a1010}.amber{color:#8a5a00}.info{color:#345}
.grade{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#666;margin-right:.3rem}
.grade.near{color:#8a5a00}
ul{margin:.25rem 0;padding-left:1.2rem}
li{margin:.25rem 0}
li .dates{color:#555;font-size:12px}
li .cite{color:#246;font-size:12px}
li .flag{display:block;color:#8a3b00;font-size:12px}
li .reason{display:block;color:#666;font-size:12px}
ol.cites{font-size:12px;color:#444}
code{font-size:12px;word-break:break-all}
.actions{display:flex;gap:.6rem;flex-wrap:wrap;margin:.5rem 0 1rem}
button{font:inherit;font-size:12px;padding:.15rem .5rem}
@media print{header,.actions{display:none}body{background:#fff}main{border:0;max-width:none;padding:0}}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _line_text(it: dict) -> str:
    bits = [f"[{it['grade']}] {it['statement']}"]
    bits.append(f"({it['dates']['text']})")
    bits.append(f"[{it.get('cite', '?')}]")
    line = " ".join(bits)
    extra = []
    if it.get("reason"):
        extra.append(f"near: {it['reason']}")
    if it.get("rule"):
        extra.append(f"rule {it['rule']}")
    if it.get("replaced_by"):
        extra.append(f"from a return since replaced; the amendment is document {str(it['replaced_by'])[:12]}…; never summed")
    if it.get("via") and it["via"] != "start":
        extra.append(f"via {it['via']}")
    for f in it.get("flags", []):
        extra.append(f"HUB: {f['text']}")
    if it.get("note") and it["view"] in ("shareholders", "directors", "disclosures"):
        extra.append(it["note"])
    return line + ("".join("\n      " + x for x in extra) if extra else "")


def text(report: dict) -> str:
    """The memo as plain text."""
    t = report["template"]
    out = [f"{t['title'].upper()} — {report['ref']}", f"template {t['name']} {t['version']} ({t['owner']}); as of {report['as_of']}; built {report['built_at']}", ""]
    if not report.get("found"):
        out.append(f"NOT FOUND: {report.get('why')}")
        return "\n".join(out) + "\n"
    s = report["subject"]
    out += ["SUBJECT", f"  {s['statement']} ({s['dates']['text']}) [{s.get('cite', 1)}]"]
    if s.get("suppressed"):
        out.append(f"  {rows.SUPPRESSED}: the row and its figures stay (hard limit 16)")
    for f in s.get("flags", []):
        out.append(f"  HUB: {f['text']}")
    g = report["group"]
    out.append("  group: " + (g.get("why") or f"{g.get('size')} rows" + (", CONTESTED as a whole" if g.get("contested") else ", not contested")
                              + (f"; {g['omitted']} rows not listed" if g.get("omitted") else "")))
    for m in report.get("members", []):
        out.append(f"  same person, by confirmed link: {m['statement']} ({m['dates']['text']}) [{m.get('cite', '?')}]"
                   + (f"\n      near: {m['reason']}" if m.get("reason") else ""))
    if report.get("problems"):
        out += ["", "REFUSED: this report breaks the presentation rules and is not to be relied on:"] + [f"  - {p}" for p in report["problems"]]
    out += ["", "FLAGS"]
    for f in report["flags"]:
        cites = f" [{', '.join(f['citations'][:8])}{'…' if len(f['citations']) > 8 else ''}]" if f["citations"] else ""
        held = f" (checked against: {'; '.join(f['sources_held'])})" if f["status"] == "clear" else ""
        nh = f" (not held: {'; '.join(f['sources_not_held'])})" if f.get("sources_not_held") else ""
        out.append(f"  {f['status'].upper():7} {f['severity']:5} {f['rule']}@{f['version']}: {f['text']}{cites}{held}{nh}")
    if not report["flags"]:
        out.append("  none: this template carries no rules")
    for sec in report["sections"]:
        out += ["", sec["heading"].upper() + f"  ({sec['confirmed']} confirmed, {sec['near']} near)"]
        if sec.get("text"):
            out.append(f"  {sec['text']}")
        if not sec["items"]:
            out.append(f"  {sec['blank']}")
        for it in sec["items"]:
            out.append("  - " + _line_text(it))
        if sec.get("omitted"):
            out.append(f"  and {sec['omitted']:,} more row(s) in {', '.join('pub.' + v for v in sec['omitted_views'])}, not listed: the walk stops at its limits")
        if sec.get("not_held") and sec["items"]:
            out.append(f"  not held: {', '.join(sec['not_held'])}")
    out += ["", "HUBS MET"]
    if report["hubs"]:
        for h in report["hubs"]:
            out.append(f"  - {h['title']} ({h['ref']}): {h['text']}")
    else:
        out.append("  none")
    w = report.get("walk", {})
    out += ["", "WHAT THE WALK LEFT OUT"]
    left = []
    if not w.get("links_built"):
        left.append("no links published: the subject is one row and every other row is a namesake, apart")
    if w.get("links_omitted"):
        left.append(f"{w['links_omitted']:,} links past the limit of {w.get('limits', {}).get('links')}")
    if w.get("entities_omitted"):
        left.append(f"{w['entities_omitted']:,} entities past the limit of {w.get('limits', {}).get('entities')}")
    if w.get("entities_not_expanded"):
        left.append(f"{w['entities_not_expanded']:,} entities named but not walked into (their other rows are not listed): the walk expands "
                    f"{w.get('limits', {}).get('expand')} at most; start a report from one of them to go on")
    if w.get("group_omitted"):
        left.append(f"{w['group_omitted']:,} rows of the group past the limit of {w.get('limits', {}).get('members')}")
    if w.get("skipped"):
        left.append("views reached but not read, because the template does not name them: " + ", ".join("pub." + v for v in w["skipped"]))
    if report.get("views_not_published"):
        left.append("views the template names that are not published: " + ", ".join("pub." + v for v in report["views_not_published"]))
    out += [f"  - {x}" for x in left] or ["  nothing: every link, entity and group row within the walk's reach is listed"]
    st = w.get("settings", {})
    if st:
        out.append(f"  settings: a connection through more than one person is {st.get('through_people')}; a hub is {st.get('hub_roles')} directorships, "
                   f"{st.get('busy_address')} companies at an address (busy), {st.get('thousand_address')} (a thousand)")
    out += ["", "NOT HELD (no lane has published these registers; nothing here says anything about them)"]
    out += [f"  - {n}" for n in report["not_held"]]
    out += ["", "KNOWN LIMITS"] + [f"  - {x}" for x in report["limits"]]
    out += ["", "CITATIONS"]
    for c in report["citations"]:
        out.append(f"  [{c['n']}] {rows.cite_text(c)}")
    out += ["", "Every connection above is as the register states it, with its date or marked undated. Two facts side by side are not a cause. "
                "Absence is not a finding: 'none found in the registers held' is the most this report says."]
    return "\n".join(out) + "\n"


# ── HTML ────────────────────────────────────────────────────────────────────

def _li(it: dict) -> str:
    out = [f'<li><span class="grade {esc(it["grade"])}">{esc(GRADE_WORD.get(it["grade"], it["grade"]))}</span>{esc(it["statement"])} '
           f'<span class="dates">({esc(it["dates"]["text"])})</span> <span class="cite">[{esc(it.get("cite", "?"))}]</span>']
    if it.get("reason"):
        out.append(f'<span class="reason">near: {esc(it["reason"])}' + (f" · rule {esc(it['rule'])}" if it.get("rule") else "") + "</span>")
    elif it.get("rule"):
        out.append(f'<span class="reason">rule {esc(it["rule"])}</span>')
    if it.get("replaced_by"):
        out.append(f'<span class="reason">from a return since replaced; the amendment is document <code>{esc(str(it["replaced_by"])[:12])}…</code>; never summed</span>')
    if it.get("via"):
        out.append(f'<span class="reason">via <a href="/report?ref={esc(it["via"])}">{esc(it["via"])}</a></span>')
    for f in it.get("flags", []):
        out.append(f'<span class="flag">hub: {esc(f["text"])}</span>')
    out.append(f'<span class="reason"><a href="/report?ref={esc(it["ref"])}">report from here</a></span></li>')
    return "".join(out)


def html_body(report: dict) -> str:
    t = report["template"]
    out = [f"<h2>{esc(t['title'])}</h2>",
           f'<p class="meta">{esc(report["ref"])} · template {esc(t["name"])} {esc(t["version"])} ({esc(t["owner"])}) · as of {esc(report["as_of"])} · built {esc(report["built_at"])}</p>']
    if not report.get("found"):
        out.append(f'<p class="warn">not found: {esc(report.get("why"))}</p>')
        return "\n".join(out)
    s = report["subject"]
    out.append("<h3>Subject</h3>")
    out.append(f'<p><strong>{esc(s["statement"])}</strong> <span class="dates">({esc(s["dates"]["text"])})</span> <span class="cite">[{esc(s.get("cite", 1))}]</span></p>')
    if s.get("suppressed"):
        out.append(f'<p class="warn">{esc(rows.SUPPRESSED)}: the row and its figures stay (hard limit 16)</p>')
    for f in s.get("flags", []):
        out.append(f'<p class="warn">hub: {esc(f["text"])}</p>')
    g = report["group"]
    out.append('<p class="note">group: ' + esc(g.get("why") or (f"{g.get('size')} rows" + (", contested as a whole" if g.get("contested") else ", not contested"))) + "</p>")
    if report.get("members"):
        out.append("<ul>" + "".join(_li(dict(m, statement="same person, by confirmed link: " + m["statement"])) for m in report["members"]) + "</ul>")
    if report.get("problems"):
        out.append('<p class="warn">Refused: this report breaks the presentation rules and is not to be relied on.</p><ul>' +
                   "".join(f"<li>{esc(p)}</li>" for p in report["problems"]) + "</ul>")
    out.append("<h3>Flags</h3><ul>")
    for f in report["flags"]:
        cites = f' <span class="cite">[{esc(", ".join(f["citations"][:8]))}{"…" if len(f["citations"]) > 8 else ""}]</span>' if f["citations"] else ""
        held = f' <span class="note">checked against: {esc("; ".join(f["sources_held"]))}</span>' if f["status"] == "clear" else ""
        nh = f' <span class="note">not held: {esc("; ".join(f["sources_not_held"]))}</span>' if f.get("sources_not_held") else ""
        out.append(f'<li><span class="{esc(f["severity"])}"><strong>{esc(f["status"])}</strong> {esc(f["severity"])}</span> {esc(f["rule"])}@{esc(f["version"])}: {esc(f["text"])}{cites}{held}{nh}</li>')
    if not report["flags"]:
        out.append("<li>none: this template carries no rules</li>")
    out.append("</ul>")
    for sec in report["sections"]:
        out.append(f'<h3>{esc(sec["heading"])} <span class="meta">{sec["confirmed"]} confirmed, {sec["near"]} near</span></h3>')
        if sec.get("text"):
            out.append(f'<p class="note">{esc(sec["text"])}</p>')
        if not sec["items"]:
            out.append(f'<p class="why">{esc(sec["blank"])}</p>')
        else:
            out.append("<ul>" + "".join(_li(it) for it in sec["items"]) + "</ul>")
            if sec.get("omitted"):
                out.append(f'<p class="note">and {sec["omitted"]:,} more row(s) in {esc(", ".join("pub." + v for v in sec["omitted_views"]))}, not listed: the walk stops at its limits</p>')
            if sec.get("not_held"):
                out.append(f'<p class="note">not held: {esc(", ".join(sec["not_held"]))}</p>')
    out.append("<h3>Hubs met</h3>")
    out.append("<ul>" + "".join(f'<li>{esc(h["title"])} <span class="meta">{esc(h["ref"])}</span>: {esc(h["text"])}</li>' for h in report["hubs"]) + "</ul>" if report["hubs"] else '<p class="why">none</p>')
    w = report.get("walk", {})
    out.append("<h3>What the walk left out</h3><ul>")
    any_left = False
    if not w.get("links_built"):
        any_left = True
        out.append("<li>no links published: the subject is one row and every other row is a namesake, apart</li>")
    for k, label in (("links_omitted", "links"), ("entities_omitted", "entities"), ("group_omitted", "rows of the group"),
                     ("entities_not_expanded", "entities named but not walked into (start a report from one of them to go on)")):
        if w.get(k):
            any_left = True
            out.append(f"<li>{w[k]:,} {label} past the walk's limit</li>")
    if w.get("skipped"):
        any_left = True
        out.append(f'<li>views reached but not read, because the template does not name them: {esc(", ".join("pub." + v for v in w["skipped"]))}</li>')
    if report.get("views_not_published"):
        any_left = True
        out.append(f'<li>views the template names that are not published: {esc(", ".join("pub." + v for v in report["views_not_published"]))}</li>')
    if not any_left:
        out.append("<li>nothing: every link, entity and group row within the walk's reach is listed</li>")
    out.append("</ul>")
    st = w.get("settings", {})
    if st:
        out.append(f'<p class="note">settings: a connection through more than one person is {esc(st.get("through_people"))}; a hub is {esc(st.get("hub_roles"))} directorships, '
                   f'{esc(st.get("busy_address"))} companies at an address (busy), {esc(st.get("thousand_address"))} (a thousand)</p>')
    out.append("<h3>Not held</h3><p class=\"note\">No lane has published these registers; nothing in this report says anything about them.</p><ul>" +
               "".join(f"<li>{esc(n)}</li>" for n in report["not_held"]) + "</ul>")
    out.append("<h3>Known limits</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in report["limits"]) + "</ul>")
    out.append('<h3>Citations</h3><ol class="cites">' + "".join(f"<li>{esc(rows.cite_text(c))}</li>" for c in report["citations"]) + "</ol>")
    out.append('<p class="note">Every connection above is as the register states it, with its date or marked undated. Two facts side by side are not a cause. '
               "Absence is not a finding: “none found in the registers held” is the most this report says. The document is cited, not opened: captured documents can carry addresses.</p>")
    return "\n".join(out)


def page(body: str, ref: str = "", template_name: str = "subject", templates: list = (), message: str = "", saved: bool = False,
         board_url: str = "") -> str:
    """The page around a memo: the form, the template choice, save; no script
    (the browser's own print command uses the print stylesheet)."""
    opts = "".join(f'<option value="{esc(n)}"{" selected" if n == template_name else ""}>{esc(n)}</option>' for n in templates) or f'<option>{esc(template_name)}</option>'
    actions = ""
    if ref:
        actions = (f'<div class="actions"><a href="/report?ref={esc(ref)}&template={esc(template_name)}&format=text">plain text</a>'
                   f'<form class="inline" method="post" action="/save"><input type="hidden" name="ref" value="{esc(ref)}">'
                   f'<input type="hidden" name="template" value="{esc(template_name)}"><input name="note" placeholder="a note to keep with it" size="28"> '
                   f'<button>{"saved" if saved else "save this memo"}</button></form></div>')
    msg = f'<span class="note">{esc(message)}</span>' if message else ""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>QueryNZ subject report</title>"
            f"<style>{CSS}</style></head><body><header><h1>QueryNZ subject report</h1>"
            f'<form method="get" action="/report"><input name="ref" value="{esc(ref)}" placeholder="register:key, as the board names a row" size="56"> '
            f'<select name="template">{opts}</select> <button>report</button></form><a href="/saved">saved memos</a>'
            + (f'<a href="{esc(board_url)}">board</a>' if board_url else "") + f"{msg}</header>"
            f"<main>{actions}{body}</main></body></html>")
