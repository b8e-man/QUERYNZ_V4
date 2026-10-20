"""The builder (plan 5.1): one row, one template, one report. It runs the
walk over the template's views, fills each section from the walk's items
(confirmed first, near after, each once), writes the blank a section with
nothing says ("none found in …" naming the views read, or "not held: …"
naming the register no lane has published), applies the template's rules,
numbers every citation, and checks the finished report against the
presentation rules (products.report.rules); the problems, if any, are
carried in the report so a surface can refuse to print it."""
from __future__ import annotations

import datetime as dt

from products.report import catalogue as cat
from products.report import rules, template as tpl, walk

SECTION_ORDER_GRADE = {"confirmed": 0, "near": 1}


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
    when = d.get("start") or d.get("on") or (dt.date(int(d["year"]), 1, 1) if d.get("year") and str(d["year"]).isdigit() else None)
    return (SECTION_ORDER_GRADE.get(it["grade"], 1), when is None, -(when.toordinal() if when else 0), it["ref"])


def build(conn, ref: str, t: tpl.Template, held: set = None) -> dict:
    """The report. `held`: the pub views present (for the blanks); read from
    the connection when not given."""
    from products.report import db
    held = held if held is not None else db.pub_views(conn)
    allowed = {v for v in t.views if v in held}
    now = dt.datetime.now().astimezone()
    report = {"template": {"name": t.name, "title": t.title, "version": t.version, "owner": t.owner,
                           "reads": [{"view": r.view, "licence": r.licence, "attribution": r.attribution, "refresh": r.refresh} for r in t.reads]},
              "ref": ref, "as_of": now.date().isoformat(), "built_at": now.isoformat(timespec="seconds"),
              "found": False, "why": "", "subject": None, "group": {}, "sections": [], "flags": [], "hubs": [], "citations": [],
              "walk": {}, "limits": list(t.limits), "not_held": [name for _, name in cat.NOT_HELD],
              "views_not_published": sorted(t.views - held), "problems": []}
    w = walk.walk(conn, ref, allowed, depth=t.depth)
    if not w.get("found"):
        report["why"] = w.get("why", "not found")
        return report
    report["found"] = True
    report["subject"] = w["start"]
    report["group"] = w["group"]
    report["hubs"] = w["hubs"]
    report["walk"] = {"links_built": w.get("links_built"), "links_omitted": w.get("links_omitted", 0), "entities_omitted": w.get("entities_omitted", 0),
                      "group_omitted": w["group"].get("omitted", 0), "skipped": w.get("skipped", []), "limits": w["limits"], "settings": w["settings"],
                      "start_outside_template": w.get("start_outside_template", False)}
    if w.get("start_outside_template"):
        report["problems"].append(f"the subject's view pub.{w['start']['view']} is not one the template {t.name} reads")
    # sections
    taken = {ref}
    members = {m["ref"] for m in w["members"]}
    for s in t.sections:
        items, omitted = [], []
        for it in _bucket_items(w, s.sources):
            if "omitted" in it:
                if it["view"] in s.views:
                    omitted.append(it)
                continue
            if it.get("missing") or it["ref"] in taken or it["view"] not in s.views:
                continue
            taken.add(it["ref"])
            items.append(it)
        # the entities the walk reached (a company, a return) belong in their section too, once
        for e in w["entities"]:
            if e["ref"] in taken or e["view"] not in s.views:
                continue
            taken.add(e["ref"])
            items.append(e)
        items.sort(key=_sort_key)
        sec = {"name": s.name, "heading": s.heading, "text": s.text, "views": list(s.views), "items": items,
               "confirmed": sum(1 for it in items if it["grade"] == "confirmed"), "near": sum(1 for it in items if it["grade"] == "near"),
               "omitted": sum(o["omitted"] for o in omitted), "omitted_views": sorted({o["view"] for o in omitted}),
               "blank": None if items else _blank(s, held), "not_held": [cat.NOT_HELD_NAME[x] for x in s.not_held]}
        report["sections"].append(sec)
    # the subject's own row and the group's members that no section claimed stay with the subject
    report["members"] = [m for m in w["members"] if m["ref"] != ref]
    # rules
    for rule in t.rules:
        try:
            report["flags"].append(rule(report))
        except Exception as exc:        # a rule that breaks is a blocked check, never a silent green
            report["flags"].append(tpl.flag(getattr(rule, "__name__", "rule"), "?", "blocked", "info",
                                            f"this check could not run: {type(exc).__name__}: {exc}"))
    report["flags"].sort(key=lambda f: (f["status"] != "fired", ("red", "amber", "info").index(f["severity"])))
    # citations, numbered once per row
    number = {}
    for it in [report["subject"]] + report["members"] + [it for s in report["sections"] for it in s["items"]]:
        c = it["citation"]
        key = (c["view"], c["key"])
        if key not in number:
            number[key] = len(number) + 1
            report["citations"].append({"n": number[key], **c})
        it["cite"] = number[key]
    report["problems"] += rules.problems(report)
    return report


def public(report: dict) -> dict:
    """The report without the rows themselves, for saving and for JSON."""
    def strip(it):
        return {k: v for k, v in it.items() if k != "row"}
    out = dict(report)
    if report.get("subject"):
        out["subject"] = strip(report["subject"])
    out["members"] = [strip(m) for m in report.get("members", [])]
    out["sections"] = [dict(s, items=[strip(it) for it in s["items"]]) for s in report["sections"]]
    return out
