"""The memo: the report printed, as plain text (for a file or a printer) and
as HTML with a print stylesheet (for the page). Answer first: the subject,
the group's standing and the flags that fired; then each section, confirmed
connections before near ones, every line with its dates and its citation
number; the hubs met; what the walk left out; what is not held; the
template's known limits; the numbered citations last. Pure: a report in, a
string out. Every value is escaped in the HTML."""
from __future__ import annotations

import html

import urllib.parse

from products.report import catalogue as cat
from products.report import contract, rows

GRADE_WORD = {"confirmed": "confirmed", "near": "near", "related": "related"}
CSS = """
body{margin:0;font:14px/1.45 system-ui,sans-serif;color:#222;background:#f4f4f2}
header{display:flex;gap:1rem;align-items:center;padding:.5rem 1rem;background:#fff;border-bottom:1px solid #ddd}
header h1{font-size:15px;margin:0 1rem 0 0;font-weight:600}
header input{padding:.3rem .5rem;font-size:14px}
header label.param{font-size:12px;color:#555}
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
p.start{margin:.1rem 0 .3rem}
ul.found{list-style:none;padding-left:0}
@media print{header,.actions{display:none}body{background:#fff}main{border:0;max-width:none;padding:0}}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _line_text(it: dict) -> str:
    bits = [("NEW " if it.get("new") else "") + f"[{it['grade']}] {it['statement']}"]
    bits.append(f"({it['dates']['text']})")
    bits.append(f"[{it.get('cite', '?')}]")
    line = " ".join(bits)
    extra = []
    if it.get("reason"):
        extra.append(f"near: {it['reason']}")
    if it.get("rule"):
        extra.append(f"rule: {cat.rule_text(it['rule'])}")
    if it.get("grade") == "related":
        extra.append(_people_text(it))
        if it.get("order") and it["order"] != "by registration date":
            extra.append(f"date order: {it['order']}")
    if it.get("replaced_by"):
        extra.append(f"from a return since replaced; the amendment is document {str(it['replaced_by'])[:12]}…; never summed")
    if it.get("via") and it["via"] != "start":
        extra.append(f"via {it['via']}")
    if it.get("above"):
        extra.append(f"on a company {it['depth']} up the chain ({it.get('through')})")
    elif it.get("depth"):
        extra.append(f"{it['depth']} up the chain" if it.get("hop_text") or it["view"] == "shareholders" else f"one step through {it.get('through')}")
    if it.get("near_link"):
        extra.append("the officer's own link to this row is near, with the link's rule and reason above")
    if it.get("hop_text"):
        extra.append(it["hop_text"])
    if (it.get("holdings") or 0) > 1:
        extra.append(f"holder of record in {it['holdings']:,} companies in the latest file")
    if it.get("changed_in"):
        extra.append(f"change first shown in the file {it['changed_in']}")
    if it.get("new") is None and it.get("since_asked"):
        extra.append("cannot say whether new: undated, or dated by a year or a file only")
    for f in it.get("flags", []):
        extra.append(f"HUB: {f['text']}")
    if it.get("note") and it["view"] in ("shareholders", "directors", "disclosures", "gazette_company_notices", "charity_officers"):
        extra.append(it["note"])
    return line + ("".join("\n      " + x for x in extra) if extra else "")


def _people_text(it: dict, cite=lambda p: f" [{p.get('cite', '?')}]") -> str:
    """The persons the links confirmed on both companies of a related link, by
    their rows on this side; the hidden counted, never named."""
    n = it.get("shared_people") or 0
    names = ", ".join(f"{p['title']}{cite(p)}" for p in it.get("people", []))
    bits = [f"{n:,} {'person' if n == 1 else 'people'} on both: " + (names or "none shown")]
    if it.get("people_hidden"):
        bits.append(f"{it['people_hidden']:,} whose name is suppressed or whose row is not found, not named")
    more = n - len(it.get("people", [])) - (it.get("people_hidden") or 0)
    if more > 0:
        bits.append(f"and {more:,} more")
    return "; ".join(bits)


def _counts(sec: dict) -> str:
    return f"{sec['related']} related" if sec.get("name") == "related" else f"{sec['confirmed']} confirmed, {sec['near']} near"


def _reaches_text(w: dict) -> list:
    """What the asked-for reaches (officers, office, chain) did and left out."""
    left = []
    if w.get("officers_omitted"):
        left.append(f"{w['officers_omitted']:,} officers past the limit of {w.get('limits', {}).get('officers')} were not followed")
    if w.get("office_companies") and not w.get("office_listed"):
        left.append(f"{w['office_companies']:,} companies share the subject's registered office: a hub, and none is listed")
    elif w.get("office_companies", 0) - 1 > w.get("office_listed", 0):
        left.append(f"{w['office_companies'] - 1:,} other companies share the subject's registered office; {w['office_listed']} listed, the walk's limit")
    c = w.get("chain") or {}
    if w.get("chain_depth") and not c.get("companies") and not c.get("unresolved"):
        left.append(f"the holding chain (to {w['chain_depth']} up): no company holder of record to follow")
    elif w.get("chain_depth"):
        bits = [f"the holding chain was followed {c.get('depth', 0)} of {w['chain_depth']} up: {c.get('companies', 0)} companies"]
        if c.get("cut"):
            bits.append(f"{c['cut']} at the depth limit go on")
        if c.get("unresolved"):
            bits.append(f"{c['unresolved']} holders not followed (a name none or several companies carry)")
        if c.get("cycles"):
            bits.append(f"{c['cycles']} met twice")
        if c.get("omitted"):
            bits.append(f"{c['omitted']} past the chain's limits")
        bits.append(f"on the companies above, {c.get('above_notices', 0)} Gazette notices and {c.get('above_directors', 0)} current directors read")
        left.append("; ".join(bits))
    for n in w.get("chain_notes") or []:
        left.append(f"chain, {n['depth']} up: {n['text']} (via {n['via']})")
    return left


def _param_text(p: dict) -> str:
    """One declared parameter as the memo states it: what the reader set, or
    that none was set and the default stands; a value that does not read as
    its kind is shown as given and said to be unread."""
    if p.get("source") == "given" and p.get("read"):
        return f"{p['name']} = {p['value']} ({p['means']})"
    if p.get("source") == "given":
        return f"{p['name']} = {p['given']!r}: not read as {'an' if p['kind'][0] in 'aeiou' else 'a'} {p['kind']}, so the rule treats it as not set ({p['means']})"
    if p.get("default") is not None:
        return f"{p['name']} not set; the template's default {p['default']} stands ({p['means']})"
    return f"{p['name']} not set ({p['means']})"


def _group_line(g: dict) -> str:
    bits = [g.get("why") or f"{g.get('size')} rows" + (", contested as a whole" if g.get("contested") else ", not contested")]
    if g.get("via") and g.get("size", 1) > 1:
        bits.append(f"{g['size']} rows" + (", contested as a whole" if g.get("contested") else ", not contested"))
    if g.get("in_sections"):
        bits.append(f"{g['in_sections']} of its rows are listed in the sections below, marked confirmed")
    if g.get("omitted"):
        bits.append(f"{g['omitted']} rows not listed")
    return "; ".join(bits)


def starts_from(report: dict) -> str:
    """Where the report starts, in plain words: the row's title, its key and
    its register by name ("This report starts from ACME LIMITED, row
    companies/9429050975815 of the register Companies, directors and
    shareholders."). The row reference itself is for addresses, never asked
    of a reader."""
    register, key = rows.split_ref(report.get("ref") or "")
    where = f"row {key} of the register {cat.REGISTER_NAME.get(register, register)}"
    s = report.get("subject") if report.get("found") else None
    return f"This report starts from {s['title']}, {where}." if s and s.get("title") else f"This report starts from {where}."


def text(report: dict) -> str:
    """The memo as plain text."""
    t = report["template"]
    out = [t['title'].upper(), starts_from(report), f"template {t['name']} {t['version']} ({t['owner']}); as of {report['as_of']}; built {report['built_at']}"]
    if report.get("since"):
        out.append(f"since {report['since']}: {report.get('new') or 0} row(s) dated on or after it are marked NEW; "
                   f"{report.get('cannot_say') or 0} cannot say (undated, or dated by a year or a monthly file only)")
    if report.get("params_declared"):
        out.append("parameters: " + "; ".join(_param_text(p) for p in report["params_declared"]))
    out.append("")
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
    out.append("  group: " + _group_line(g).replace("contested as a whole", "CONTESTED as a whole"))
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
        out += ["", sec["heading"].upper() + f"  ({_counts(sec)})"]
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
    for x in report.get("superseded_not_held") or []:
        left.append(f"the template names as not held a register that is published and which it does not read: {x}")
    left += _reaches_text(w)
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

def _li(it: dict, template_name: str = "subject") -> str:
    out = [f'<li>{"<span class=\"warn\">new</span> " if it.get("new") else ""}<span class="grade {esc(it["grade"])}">{esc(GRADE_WORD.get(it["grade"], it["grade"]))}</span>{esc(it["statement"])} '
           f'<span class="dates">({esc(it["dates"]["text"])})</span> <span class="cite">[{esc(it.get("cite", "?"))}]</span>']
    if it.get("reason"):
        out.append(f'<span class="reason">near: {esc(it["reason"])}' + (f" · rule: {esc(cat.rule_text(it['rule']))}" if it.get("rule") else "") + "</span>")
    elif it.get("rule"):
        out.append(f'<span class="reason">rule: {esc(cat.rule_text(it["rule"]))}</span>')
    if it.get("grade") == "related":
        out.append(f'<span class="reason">{esc(_people_text(it))}</span>')
        if it.get("order") and it["order"] != "by registration date":
            out.append(f'<span class="reason">date order: {esc(it["order"])}</span>')
    if it.get("replaced_by"):
        out.append(f'<span class="reason">from a return since replaced; the amendment is document <code>{esc(str(it["replaced_by"])[:12])}…</code>; never summed</span>')
    if it.get("via"):
        out.append(f'<span class="reason">via <a href="{esc(contract.report_url(it["via"], "", template_name))}">{esc(it["via"])}</a></span>')
    if it.get("above"):
        out.append(f'<span class="reason">on a company {esc(it["depth"])} up the chain (<a href="{esc(contract.report_url(it["through"], "", template_name))}">{esc(it["through"])}</a>)</span>')
    elif it.get("depth"):
        out.append(f'<span class="reason">{esc(f"{it[chr(100)+chr(101)+chr(112)+chr(116)+chr(104)]} up the chain" if it.get("hop_text") or it["view"] == "shareholders" else f"one step through {it.get(chr(116)+chr(104)+chr(114)+chr(111)+chr(117)+chr(103)+chr(104))}")}</span>')
    if it.get("near_link"):
        out.append('<span class="reason">the officer\'s own link to this row is near, with the link\'s rule and reason above</span>')
    if it.get("hop_text"):
        out.append(f'<span class="reason">{esc(it["hop_text"])}</span>')
    if (it.get("holdings") or 0) > 1:
        out.append(f'<span class="reason">holder of record in {it["holdings"]:,} companies in the latest file</span>')
    if it.get("changed_in"):
        out.append(f'<span class="reason">change first shown in the file {esc(it["changed_in"])}</span>')
    for f in it.get("flags", []):
        out.append(f'<span class="flag">hub: {esc(f["text"])}</span>')
    out.append(f'<span class="reason"><a href="{esc(contract.report_url(it["ref"], "", template_name))}">report from here</a></span></li>')
    return "".join(out)


def html_body(report: dict) -> str:
    t = report["template"]
    out = [f"<h2>{esc(t['title'])}</h2>",
           f'<p class="start">{esc(starts_from(report))}</p>',
           f'<p class="meta">template {esc(t["name"])} {esc(t["version"])} ({esc(t["owner"])}) · as of {esc(report["as_of"])} · built {esc(report["built_at"])}</p>']
    if report.get("since"):
        out.append(f'<p class="meta">since {esc(report["since"])}: {report.get("new") or 0} row(s) dated on or after it are marked new; '
                   f'{report.get("cannot_say") or 0} cannot say (undated, or dated by a year or a monthly file only)</p>')
    if report.get("params_declared"):
        out.append('<p class="meta">parameters: ' + esc("; ".join(_param_text(p) for p in report["params_declared"])) + "</p>")
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
    out.append('<p class="note">group: ' + esc(_group_line(g)) + "</p>")
    if report.get("members"):
        out.append("<ul>" + "".join(_li(dict(m, statement="same person, by confirmed link: " + m["statement"]), t["name"]) for m in report["members"]) + "</ul>")
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
        out.append(f'<h3>{esc(sec["heading"])} <span class="meta">{esc(_counts(sec))}</span></h3>')
        if sec.get("text"):
            out.append(f'<p class="note">{esc(sec["text"])}</p>')
        if not sec["items"]:
            out.append(f'<p class="why">{esc(sec["blank"])}</p>')
        else:
            out.append("<ul>" + "".join(_li(it, t["name"]) for it in sec["items"]) + "</ul>")
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
    for x in report.get("superseded_not_held") or []:
        any_left = True
        out.append(f"<li>the template names as not held a register that is published and which it does not read: {esc(x)}</li>")
    for x in _reaches_text(w):
        any_left = True
        out.append(f"<li>{esc(x)}</li>")
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


def _param_inputs(params: list) -> str:
    """The form's inputs for the parameters the chosen template declares: one
    each, named as declared, its meaning as the label, what the reader gave
    as its value and its default as the placeholder."""
    out = []
    for p in params or ():
        ph = "" if p.get("default") is None else f'placeholder="{esc(p["default"])}" '
        out.append(f'<label class="param" title="{esc(p.get("means"))}">{esc(p["name"])} '
                   f'<input name="{esc(p["name"])}" value="{esc(p.get("given") or "")}" {ph}size="8"></label>')
    return " ".join(out)


def report_href(ref: str, template_name: str = "subject", since: str = "", params: list = ()) -> str:
    """The address that runs the report on a row with the chosen template,
    the since date and the parameters the reader gave (unescaped)."""
    url = contract.report_url(ref, "", template_name)
    q = urllib.parse.urlencode([("since", since)] * bool(since) + [(p["name"], p["given"]) for p in params or () if p.get("given")])
    return url + (("&" if "?" in url else "?") + q if q else "")


def search_results(term: str, found: list, template_name: str = "subject", since: str = "", params: list = ()) -> str:
    """The rows a name search found ([(view, total, rows)], products/report/search.py),
    each a link that runs the report on that row; up to ten a view, with the view's count."""
    if not found:
        return (f"<h2>No row found for “{esc(term)}”</h2><p class=\"note\">Every word must begin a word of a name the published registers hold, "
                "macrons folded (“hart” finds Hart and Hartley). Fewer words, or another spelling, may find it. "
                "A suppressed name is never found by name.</p>")
    out = [f"<h2>Rows naming “{esc(term)}”</h2><p class=\"note\">Choose a row: the report starts from it. "
           "One name in several registers is not yet one person; the report says what joins them.</p>"]
    for v, total, rs in found:
        more = f", the first {len(rs)} listed" if total > len(rs) else ""
        out.append(f"<h3>{esc(cat.REGISTER_NAME.get(v.register, v.register))}: {esc(v.name.replace('_', ' '))} "
                   f"<span class=\"meta\">{total:,} found{more}</span></h3><ul class=\"found\">")
        for r in rs:
            ref = rows.ref_of(v, str(r["key"]))
            d = rows.dates(v, r)
            out.append(f'<li><a href="{esc(report_href(ref, template_name, since, params))}">{esc(rows.title(v, r))}</a> '
                       f'<span class="dates">{esc(d.get("text"))}</span></li>')
        out.append("</ul>")
    return "\n".join(out)


def page(body: str, ref: str = "", template_name: str = "subject", templates: list = (), message: str = "", saved: bool = False,
         board_url: str = "", since: str = "", params: list = (), term: str = "") -> str:
    """The page around a memo: the name search, the template choice, the
    since date, the parameters the template declares, save; no script (the
    browser's own print command uses the print stylesheet). The search is
    a GET form to the start page, which lists the rows it finds; the
    report's own row reference travels only in addresses."""
    opts = "".join(f'<option value="{esc(n)}"{" selected" if n == template_name else ""}>{esc(n)}</option>' for n in templates) or f'<option>{esc(template_name)}</option>'
    actions = ""
    hidden = "".join(f'<input type="hidden" name="{esc(p["name"])}" value="{esc(p["given"])}">' for p in params or () if p.get("given"))
    if ref:
        q = "&".join(f"{esc(p['name'])}={esc(p['given'])}" for p in params or () if p.get("given"))
        actions = (f'<div class="actions"><a href="/report?ref={esc(ref)}&template={esc(template_name)}&format=text'
                   f'{"&since=" + esc(since) if since else ""}{"&" + q if q else ""}">plain text</a>'
                   f'<form class="inline" method="post" action="/save"><input type="hidden" name="ref" value="{esc(ref)}">'
                   f'<input type="hidden" name="template" value="{esc(template_name)}"><input type="hidden" name="since" value="{esc(since)}">{hidden}'
                   f'<input name="note" placeholder="a note to keep with it" size="28"> '
                   f'<button>{"saved" if saved else "save this memo"}</button></form>'
                   f'<form class="inline" method="get" action="{esc(contract.report_url(ref))}"><select name="template">{opts}</select> '
                   f'<input type="hidden" name="since" value="{esc(since)}"><button>run with this template</button></form></div>')
    msg = f'<span class="note">{esc(message)}</span>' if message else ""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>QueryNZ subject report</title>"
            f"<style>{CSS}</style></head><body><header><h1>QueryNZ subject report</h1>"
            f'<form method="get" action="/"><input name="q" value="{esc(term)}" placeholder="a person, company or organisation name" '
            f'aria-label="a person, company or organisation name" size="40"> '
            f'<select name="template">{opts}</select> <label class="param" title="rows dated on or after this day are marked new">since '
            f'<input name="since" value="{esc(since)}" placeholder="YYYY-MM-DD" size="10"></label> {_param_inputs(params)} <button>search</button></form>'
            f'<a href="/saved">saved memos</a>'
            + (f'<a href="{esc(board_url)}">board</a>' if board_url else "") + f"{msg}</header>"
            f"<main>{actions}{body}</main></body></html>")
