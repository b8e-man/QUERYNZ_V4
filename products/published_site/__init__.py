"""The published-site shape, begun (plan 1.11): one plain page from one
published table. The template says what it reads and what it cannot see;
the shape renders. Rules for everything a product shows (contract: a
template): every figure names its document; a blank says why; a total
states what it leaves out; a figure read from pixels is marked.

    render_party_totals(rows, template) -> str
"""
import datetime as dt
import json
import os
from collections import defaultdict
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "templates", "party_totals.json")


def template(path: str = None):
    """The template as data. A shape reads its template file itself (imports
    run one way: a shape reaches only support); the templates module's own
    tests hold it to the contract."""
    with open(path or TEMPLATE, encoding="utf-8") as f:
        d = json.load(f)
    return SimpleNamespace(name=d["name"], version=int(d.get("version", 0)), owner=d.get("owner", ""),
                           sections=tuple(d.get("sections", [])), known_limits=d.get("known_limits", ""),
                           reads=tuple(SimpleNamespace(**r) for r in d.get("reads", [])), settings=d.get("settings", {}))


def money(x) -> str:
    return f"${float(x):,.2f}"


def render_party_totals(rows: list, template, now: dt.datetime = None) -> str:
    """rows: dicts from pub.party_return_totals. One line per return,
    grouped by party and year; a party-year with several returns held
    shows every one and chooses none."""
    now = now or dt.datetime.now().astimezone()
    by_party = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_party[r.get("party") or f"(unresolved: {r.get('party_label')})"][int(r["year"])].append(r)
    out = [f"{template.sections[0] if template.sections else 'Declared party donations by year'}",
           f"{template.name} v{template.version}, {template.owner}. Printed {now:%d %B %Y %H:%M}. "
           f"Reads {', '.join(x.table for x in template.reads)}.", ""]
    if not rows:
        out.append("No returns read yet: the table is empty.")
    for party in sorted(by_party):
        out.append(party)
        for year in sorted(by_party[party]):
            held = by_party[party][year]
            note = f"  ({len(held)} returns held for this year; none chosen)" if len(held) > 1 else ""
            for r in held:
                basis = "declared total" + (f", parts printed as {r['declared_parts']}" if r.get("declared_parts") else "")
                how = "read from the text layer" if r.get("read_from") == "text" else "READ FROM PIXELS: weaker evidence"
                check = "declared NIL" if r.get("total_check") == "declared-nil" else "equals its parts as printed"
                out.append(f"  {year}  {money(r['declared_total']):>16}  {basis}, {how}, {check}{note}")
                out.append(f"        document {r['document']}  page {r.get('page', 1)}")
        out.append("")
    out.append(f"{len(rows)} returns read. A total here is the party's own grand total on its declaration page; "
               "it leaves out loans and anything the party did not declare.")
    out.append("")
    out.append("Known limits: " + template.known_limits)
    return "\n".join(out) + "\n"
