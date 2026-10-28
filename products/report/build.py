"""The builder (plan 5.1): one row, one template, one report. It runs the
walk over the template's views, fills each section from the walk's items
(confirmed first, near after, each once; a section's own, status and
changed filters applied, so a row one section leaves goes on to the next
that names its view), writes the blank a section with nothing says ("none
found in …" naming the views read, or "not held: …" naming the register
no lane has published), applies the template's rules, numbers every
citation, marks what is new since a date when one is given, and checks the
finished report against the presentation rules (products.report.rules);
the problems, if any, are carried in the report so a surface can refuse to
print it."""
from __future__ import annotations

import datetime as dt
import time

from products.report import catalogue as cat
from products.report import contract, rules, template as tpl, walk

SECTION_ORDER_GRADE = {"confirmed": 0, "near": 1}
#: the shape's own section for the links lane's third grade (ruling 106 (2)), added to every template's report when the walk
#: met a related link, after the template's section that lists companies: a relation between two entities, stated in words,
#: never listed with the confirmed (one entity) or the near (perhaps one)
RELATED_SECTION = {"name": "related", "heading": "Related companies: one succeeded by another",
                   "text": "Each line is two companies, two entities, in date order, under one name: the earlier succeeded by the later "
                           "where one carries a year in brackets, or delisted and refiled where one was removed and the other registered "
                           "within twelve months (ruling 109); in each a person the links confirm on both. A relation between two "
                           "companies, never the same company; neither is walked from the other, so each has its own report."}
FILE_VIEWS = frozenset({"directors", "shareholders", "company_addresses", "companies"})   # rows dated by the monthly files they were seen in
_FILES = {"at": 0.0, "first": None, "last": None}
FILES_TTL_S = 3600


def files_held(conn) -> tuple:
    """(first file, last file) the companies lane holds, read from pub.companies
    once an hour: the lane publishes no list of its files
    (`the-companies-lane-publishes-no-list-of-its-monthly-files`)."""
    if time.monotonic() - _FILES["at"] > FILES_TTL_S or _FILES["first"] is None:
        got = walk.db.rows(conn, "select min(first_file) as first, max(last_file) as last from pub.companies")
        _FILES.update(at=time.monotonic(), first=(got[0]["first"] if got else None), last=(got[0]["last"] if got else None))
    return _FILES["first"], _FILES["last"]


def changed_in(it: dict, files: tuple) -> str | None:
    """The file that first shows the change this row is, or None when the row
    is no change: a row that arrived after the first file held, one that left
    before the latest, or a company's earlier state."""
    r = it.get("row") or {}
    first, last = files
    if it["view"] == "company_states":
        return str(r.get("file") or "")
    if it["view"] not in FILE_VIEWS:
        return None
    if r.get("first_file") and first and str(r["first_file"]) > str(first):
        return str(r["first_file"])
    if "in_latest" in r and not r.get("in_latest") and r.get("last_file"):
        return str(r["last_file"])
    return None


def is_own(it: dict, ref: str, members: set) -> bool:
    return it["ref"] == ref or it.get("via") in members or it.get("via") == ref


def is_new(it: dict, since: dt.date | None):
    """True when a date of the row is on or after `since`; False when every
    date is before it; None when the row is undated, or dated only by a year
    or by the files it was seen in, so it cannot say."""
    if since is None:
        return None
    d = it.get("dates") or {}
    when = [x for x in (d.get("start"), d.get("end"), d.get("on"), d.get("filed"), d.get("published")) if x]
    when = [x.date() if isinstance(x, dt.datetime) else x for x in when]
    if not when:
        return None
    return any(x >= since for x in when)


def _bucket_items(w: dict, sources: tuple) -> list:
    out = []
    for b in sources:
        for it in w.get(b, []):
            out.append(it)
    return out


def _blank(section: tpl.Section, held: set) -> str:
    nh = [cat.NOT_HELD_NAME[x] for x in section.not_held]
    read = [cat.REGISTER_NAME.get(cat.BY_NAME[v].register, v) for v in section.views if v in held]
    read = sorted(set(read))
    missing = sorted({v for v in section.views if v not in held})
    bits = []
    if read:
        bits.append("none found in " + ", ".join(read))
    if missing:
        bits.append("not held: " + ", ".join(f"pub.{v}" for v in missing) + " is not published")
    if nh:
        bits.append("not held: " + ", ".join(nh))
    return "; ".join(bits) or "none found"


def _sort_key(it: dict) -> tuple:
    d = it["dates"]
    when = d.get("start") or d.get("on") or d.get("published") or (dt.date(int(d["year"]), 1, 1) if d.get("year") and str(d["year"]).isdigit() else None)
    return (SECTION_ORDER_GRADE.get(it["grade"], 1), when is None, -(when.toordinal() if when else 0), it["ref"])


def _ordered(items: list) -> list:
    """Confirmed before near; an entity (a company, a return) before the rows
    that sit on it, each group newest first; rows whose entity is not in the
    section after, newest first."""
    refs = {it["ref"] for it in items}
    heads = sorted([it for it in items if it["view"] in ("companies", "societies", "charities", "party_return_totals", "candidate_return_totals", "disclosures",
                                                         "promoters", "mp_interest_returns", "parties")], key=_sort_key)
    head_refs = {h["ref"] for h in heads}
    out, placed = [], set()
    for h in heads:
        out.append(h)
        placed.add(h["ref"])
        for it in sorted([x for x in items if x.get("via") == h["ref"] and x["ref"] not in head_refs], key=_sort_key):
            out.append(it)
            placed.add(it["ref"])
    rest = sorted([x for x in items if x["ref"] not in placed], key=_sort_key)
    # keep confirmed before near overall: a near head and its rows sit after every confirmed item
    conf = [x for x in out + rest if x["grade"] == "confirmed"]
    nearby = [x for x in out + rest if x["grade"] != "confirmed"]
    return conf + nearby


def apply_rules(report: dict, t: tpl.Template) -> list:
    """The flags: the contract's common rules first (unless the template opts
    out), then the template's own; a template flag with a common flag's
    `rule` name replaces it. A rule that breaks is a blocked check, never a
    silent green. Fired first, red before amber before info."""
    flags = {}
    for rule in (contract.COMMON_RULES if t.common_rules else ()) + tuple(t.rules):
        try:
            f = rule(report)
        except Exception as exc:
            f = contract.flag(getattr(rule, "__name__", "rule"), "?", "blocked", "info", f"this check could not run: {type(exc).__name__}: {exc}")
        flags[f["rule"]] = f
    out = list(flags.values())
    out.sort(key=lambda f: (f["status"] != "fired", ("red", "amber", "info").index(f["severity"])))
    return out


def _keeps(s: tpl.Section, it: dict, ref: str, members: set, files: tuple) -> bool:
    """The section's own filters: own, statuses, changed."""
    if s.own is not None and is_own(it, ref, members) != s.own:
        return False
    if s.statuses and "status" in (it.get("row") or {}) and cat.fold(str(it["row"].get("status") or "")) not in s.statuses:
        return False
    if s.changed:
        when = changed_in(it, files)
        if when is None:
            return False
        it["changed_in"] = when
    return True


def build(conn, ref: str, t: tpl.Template, held: set = None, since: dt.date | str | None = None, params: dict | None = None) -> dict:
    """The report. `held`: the pub views present (for the blanks); read from
    the connection when not given. `since`: a date; every item dated on or
    after it is marked new, one that cannot say is marked so, and a rule may
    read `report["since"]`. `params`: {name: value} the reader set, each a
    parameter the template declares (`[[params]]` in its template.toml; an
    undeclared name is refused with KeyError before anything is read): every
    declared parameter is put in `report["params"]` and under its own name
    on the report, read as its kind, or as the text given when that does
    not read (the rule says so), or its default."""
    from products.report import db
    values, declared = tpl.params_for(t, params)
    held = held if held is not None else db.pub_views(conn)
    allowed = {v for v in t.views if v in held}
    if isinstance(since, str):
        since = dt.date.fromisoformat(since.strip()) if since.strip() else None
    now = dt.datetime.now().astimezone()
    report = {"template": {"name": t.name, "title": t.title, "version": t.version, "owner": t.owner,
                           "reads": [{"view": r.view, "licence": r.licence, "attribution": r.attribution, "refresh": r.refresh} for r in t.reads]},
              "ref": ref, "as_of": now.date().isoformat(), "built_at": now.isoformat(timespec="seconds"),
              "since": since.isoformat() if since else None, "new": None,
              "params": values, "params_declared": list(declared), **values,
              "found": False, "why": "", "subject": None, "group": {}, "sections": [], "flags": [], "hubs": [], "citations": [],
              "walk": {}, "limits": list(t.limits), "not_held": [name for _, name in cat.NOT_HELD],
              "superseded_not_held": [f"{cat.REGISTER_NAME[reg]} (named {key!r} in the template; published as "
                                      f"{', '.join('pub.' + v.name for v in cat.views_of(reg))})" for key, reg in t.superseded_not_held],
              "views_not_published": sorted(t.views - held), "problems": []}
    w = walk.walk(conn, ref, allowed, depth=t.depth, buckets=t.buckets, chain_depth=t.chain_depth)
    if not w.get("found"):
        report["why"] = w.get("why", "not found")
        return report
    report["found"] = True
    report["subject"] = w["start"]
    report["group"] = w["group"]
    report["hubs"] = w["hubs"]
    report["walk"] = {"links_built": w.get("links_built"), "links_omitted": w.get("links_omitted", 0), "entities_omitted": w.get("entities_omitted", 0),
                      "entities_not_expanded": w.get("entities_not_expanded", 0),
                      "group_omitted": w["group"].get("omitted", 0), "skipped": w.get("skipped", []), "limits": w["limits"], "settings": w["settings"],
                      "start_outside_template": w.get("start_outside_template", False), "buckets": sorted(t.buckets),
                      "officers_followed": w.get("officers_followed", 0), "officers_omitted": w.get("officers_omitted", 0),
                      "office_companies": w.get("office_companies", 0), "office_listed": w.get("office_listed", 0),
                      "chain_depth": t.chain_depth, "chain": w.get("chain_stats") or {},
                      "chain_notes": [{"text": x["chain_note"], "via": x["via"], "depth": x["depth"]} for x in w.get("chain", []) if "chain_note" in x]}
    if w.get("start_outside_template"):
        report["problems"].append(f"the subject's view pub.{w['start']['view']} is not one the template {t.name} reads")
    # sections
    taken = {ref}
    members = {m["ref"] for m in w["members"]} | {ref}
    files = files_held(conn) if any(s.changed for s in t.sections) else (None, None)
    for s in t.sections:
        items, omitted = [], []
        for it in _bucket_items(w, s.sources):
            if "omitted" in it:
                if it["view"] in s.views:
                    omitted.append(it)
                continue
            if "chain_note" in it:
                continue
            if it.get("missing") or it["ref"] in taken or it["view"] not in s.views or not _keeps(s, it, ref, members, files):
                continue
            taken.add(it["ref"])
            items.append(it)
        # the entities the walk reached (a company, a return) belong in their section too, once
        for e in w["entities"]:
            if e["ref"] in taken or e["view"] not in s.views or not _keeps(s, e, ref, members, files):
                continue
            taken.add(e["ref"])
            items.append(e)
        if s.changed:   # the file that first shows the change, newest first; confirmed before near
            items.sort(key=lambda it: (it.get("changed_in") or "", it["ref"]), reverse=True)
            items.sort(key=lambda it: SECTION_ORDER_GRADE.get(it["grade"], 1))
        else:
            items = _ordered(items)
        for it in items:
            it["new"] = is_new(it, since)
        sec = {"name": s.name, "heading": s.heading, "text": s.text, "views": list(s.views), "items": items,
               "confirmed": sum(1 for it in items if it["grade"] == "confirmed"), "near": sum(1 for it in items if it["grade"] == "near"),
               "omitted": sum(o["omitted"] for o in omitted), "omitted_views": sorted({o["view"] for o in omitted}),
               "blank": None if items else _blank(s, held), "not_held": [cat.NOT_HELD_NAME[x] for x in s.not_held],
               "own": s.own, "statuses": list(s.statuses), "changed": s.changed,
               "new": sum(1 for it in items if it.get("new")) if since else None,
               "cannot_say": sum(1 for it in items if it.get("new") is None) if since else None}
        report["sections"].append(sec)
    if w.get("related"):
        report["sections"].insert(_related_at(report["sections"]), related_section(w["related"], since))
    if since:
        report["new"] = sum(s["new"] for s in report["sections"])
        report["cannot_say"] = sum(s["cannot_say"] for s in report["sections"])
    # the group's members that no section claimed stay with the subject in the header; the rest are in their sections, once
    report["members"] = [m for m in w["members"] if m["ref"] != ref and m["ref"] not in taken]
    report["group"]["in_sections"] = sum(1 for m in w["members"] if m["ref"] != ref and m["ref"] in taken)
    report["flags"] = apply_rules(report, t)
    # citations, numbered once per row
    number = {}
    for it in [report["subject"]] + report["members"] + [x for s in report["sections"] for it in s["items"] for x in [it] + it.get("people", [])]:
        c = it["citation"]
        key = (c["view"], c["key"])
        if key not in number:
            number[key] = len(number) + 1
            report["citations"].append({"n": number[key], **c})
        it["cite"] = number[key]
    report["problems"] += rules.problems(report)
    return report


def _related_at(sections: list) -> int:
    """Where the related section goes: after the first section that lists
    companies, else last."""
    for i, s in enumerate(sections):
        if "companies" in s["views"]:
            return i + 1
    return len(sections)


def related_section(items: list, since: dt.date | None) -> dict:
    """The related links as their own section, earliest company first: never
    counted confirmed or near."""
    items = sorted(items, key=lambda it: (it["earlier"], it["later"]))
    for it in items:
        it["new"] = is_new(it, since)
        for p in it.get("people", []):
            p["new"] = is_new(p, since)
    return {**RELATED_SECTION, "views": ["companies"], "items": items, "confirmed": 0, "near": 0, "related": len(items),
            "omitted": 0, "omitted_views": [], "blank": None, "not_held": [], "own": None, "statuses": [], "changed": False,
            "new": sum(1 for it in items if it.get("new")) if since else None,
            "cannot_say": sum(1 for it in items if it.get("new") is None) if since else None}


def public(report: dict) -> dict:
    """The report without the rows themselves, for saving and for JSON."""
    def strip(it):
        return {k: ([strip(p) for p in v] if k == "people" else v) for k, v in it.items() if k != "row"}
    out = dict(report)
    if report.get("subject"):
        out["subject"] = strip(report["subject"])
    out["members"] = [strip(m) for m in report.get("members", [])]
    out["sections"] = [dict(s, items=[strip(it) for it in s["items"]]) for s in report["sections"]]
    return out
