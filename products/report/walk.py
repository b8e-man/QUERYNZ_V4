"""The walk outward from one row (plan 5.1): the group the row belongs to
(`pub.groups`), the confirmed links that make it and the near links beside
them with their reasons (`pub.links`), the entities the group's rows sit on
(a company, a society, a return, a promoter), the register's own rows on
each entity (its directors, shareholders, registered office, donors), and
one step further: the other people on those entities, listed as near,
never confirmed, because a connection through more than one person is near
by the design's default. Every item is a published row with its own dates;
a hop is dated by the role row that makes it, or marked undated.

Hubs are flagged as the walk meets them: a person whose group holds many
directorships (a professional director), a holder whose name says nominee
or trustee, the Crown, and a registered office shared by a busy or a
thousand companies. A hub is still walked; the flag tells the reader why
what it joins means little.

Nothing here reads a view the template did not name: `allowed` is the
template's list and a view outside it is skipped, with the skip recorded.
Limits are declared in the result, never silent: what the walk left out is
counted (lesson L708 of the old estate: a cut-off chain must say it goes on).
Reads `pub.*` only, on the product reader."""
from __future__ import annotations

import re

from products.report import catalogue as cat
from products.report import db, rows

LIMITS = {"members": 300, "links": 400, "roles": 200, "entities": 40, "second": 300, "expand": 12}
SETTINGS = {"hub_roles": 50, "busy_address": 50, "thousand_address": 1000,
            "through_people": "near"}   # design: a connection through more than one person is near, never confirmed

NEAR_THROUGH_PEOPLE = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"
NEAR_CONTESTED_GROUP = "the group this row belongs to is contested as a whole: the watch flagged it"
NEAR_THROUGH_NEAR = "reached through a near link: {reason}"
NOMINEE = re.compile(r"\b(nominees?|trustees?|custodians?|custodial)\b", re.I)
CROWN = re.compile(r"\b(her majesty|his majesty|the crown|the sovereign|minister (of|for)|crown entity)\b", re.I)

#: the register's own rows on an entity: (child view, column holding the entity's key, order)
ROLES_ON = {
    "companies": (("directors", "entity_key", "appointed_on"), ("shareholders", "entity_key", "name"),
                  ("company_addresses", "entity_key", "started_on")),
    "societies": (("society_officers", "society_key", "started_on"),),
    "party_return_totals": (("party_return_donors", "return_key", "ordinal"), ("party_return_loans", "return_key", "ordinal")),
    "candidate_return_totals": (("candidate_return_donors", "return_key", "ordinal"),),
    "disclosures": (("disclosure_items", "declaration", "ordinal"),),
    "promoters": (("promoter_people", "promoter_key", "role"),),
    "mp_interest_returns": (("mp_interests", "member_return", "key"),),
}
#: entities expanded only when they are the start row: a return's other donors are not the subject's connections
EXPAND_ONLY_AS_START = frozenset({"party_return_totals", "candidate_return_totals", "disclosures", "mp_interest_returns"})
#: rows of other views that point at a company by its register key
POINTING_AT = {"companies": (("gazette_liquidations", "register_key", "published_on"),
                             ("gazette_company_notices", "register_key", "published_on"))}


# ── items ───────────────────────────────────────────────────────────────────

def item(v: cat.View, r: dict, entity_title: str = None, **extra) -> dict:
    """One row as the report carries it: ref, title, statement, dates,
    citation, grade and reason, flags. The row itself is kept for the
    template's rules; the memo never prints it whole."""
    it = {"ref": rows.ref_of(v, str(r.get(v.key_col))), "view": v.name, "register": v.register, "kind": v.kind,
          "title": rows.title(v, r), "statement": rows.statement(v, r, entity_title), "dates": rows.dates(v, r),
          "citation": rows.citation(v, r), "suppressed": rows.is_suppressed(v, r), "note": v.note,
          "grade": "confirmed", "reason": None, "rule": None, "via": None, "flags": [], "row": r}
    it.update(extra)
    return it


def near(it: dict, reason: str, rule: str = None) -> dict:
    it["grade"], it["reason"] = "near", reason
    if rule:
        it["rule"] = rule
    return it


def flag(kind: str, text: str, evidence=None) -> dict:
    return {"kind": kind, "text": text, "evidence": evidence}


# ── reading the links tables ────────────────────────────────────────────────

def links_built(conn) -> bool:
    return db.has_relation(conn, "pub", "links")


def group_of(conn, ref: str) -> dict:
    """{'built', 'why', 'group_id', 'contested', 'settings', 'rows', 'size', 'omitted'}."""
    if not db.has_relation(conn, "pub", "groups"):
        return {"built": False, "why": "no groups built yet: links/ has published nothing", "rows": [ref], "size": 1,
                "contested": False, "omitted": 0, "group_id": None, "settings": None}
    mine = db.rows(conn, "select * from pub.groups where row_key = %s", (ref,))
    if not mine:
        return {"built": True, "why": "this row is in no group: no confirmed link reaches it", "rows": [ref], "size": 1,
                "contested": False, "omitted": 0, "group_id": None, "settings": None}
    g = mine[0]
    got = db.rows(conn, "select row_key, count(*) over () as total from pub.groups where group_id = %s order by row_key limit %s",
                  (g["group_id"], LIMITS["members"]))
    size = got[0]["total"] if got else 1
    return {"built": True, "why": "", "group_id": g["group_id"], "contested": bool(g.get("contested")), "settings": g.get("settings"),
            "rows": [x["row_key"] for x in got], "size": size, "omitted": max(0, size - len(got))}


def links_of(conn, refs: list) -> dict:
    """{'built', 'confirmed': [...], 'near': [...], 'omitted'}: every link
    touching any of the refs; each: this, other, rule, evidence, grade,
    reason, watch, decision."""
    if not links_built(conn) or not refs:
        return {"built": links_built(conn), "confirmed": [], "near": [], "omitted": 0}
    got = db.rows(conn, "select *, count(*) over () as total from pub.links where row_a = any(%s) or row_b = any(%s) "
                        "order by grade, rule, row_a, row_b limit %s", (refs, refs, LIMITS["links"]))
    total = got[0]["total"] if got else 0
    mine = set(refs)
    out = {"built": True, "confirmed": [], "near": [], "omitted": max(0, total - len(got))}
    for l in got:
        this, other = (l["row_a"], l["row_b"]) if l["row_a"] in mine else (l["row_b"], l["row_a"])
        grade = l["grade"] if l["grade"] in ("confirmed", "near") else "near"
        out[grade].append({"this": this, "other": other, "rule": l["rule"], "evidence": l.get("evidence"), "grade": grade,
                           "reason": l.get("reason"), "watch": l.get("watch") or [], "decision": l.get("decision")})
    return out


def resolve(conn, ref: str, cache: dict):
    """(view, row) for a ref, cached across the walk, or None."""
    if ref not in cache:
        v, r = rows.locate(conn, ref)
        cache[ref] = (v, r) if r else None
    return cache[ref]


# ── hubs ────────────────────────────────────────────────────────────────────

def name_hub(name: str) -> dict | None:
    if not name:
        return None
    if CROWN.search(name):
        return flag("crown", "the Crown: a hub that joins thousands of rows; a connection through it means little on its own", name)
    if NOMINEE.search(name):
        return flag("nominee", "a nominee or trustee holder: it holds as the register states, for others; it is shown as a "
                               "holder of record and never as an owner", name)
    return None


def role_counts(conn, refs: list) -> dict:
    """{ref: (group_id, directorships in that group)} for person rows, in two
    queries: a lone row counts its own directorships (one or none)."""
    if not refs or not db.has_relation(conn, "pub", "names"):
        return {}
    got = db.rows(conn, "select n.ref, n.view, g.group_id from pub.names n left join pub.groups g on g.row_key = n.ref where n.ref = any(%s)", (refs,))
    groups = sorted({x["group_id"] for x in got if x["group_id"]})
    counts = {}
    if groups:
        for x in db.rows(conn, "select g.group_id, count(*) as n from pub.groups g join pub.names n on n.ref = g.row_key "
                               "where g.group_id = any(%s) and n.view = 'directors' group by 1", (groups,)):
            counts[x["group_id"]] = x["n"]
    out = {}
    for x in got:
        gid = x["group_id"]
        out[x["ref"]] = (gid, counts.get(gid, 1 if x["view"] == "directors" else 0))
    return out


def flag_people(conn, items: list) -> None:
    """Flags a professional director (a group with `hub_roles` directorships
    or more) and a name that says nominee, trustee or the Crown."""
    counts = role_counts(conn, [it["ref"] for it in items if it["kind"] == "person"])
    for it in items:
        gid, n = counts.get(it["ref"], (None, 0))
        if n >= SETTINGS["hub_roles"]:
            it["flags"].append(flag("professional-director", f"a professional director: this person's group holds {n:,} directorships; "
                                                             f"a shared board with them joins little", {"group": gid, "directorships": n}))
        h = name_hub(it["row"].get("name") or it["row"].get("full_name") or "") if not it["suppressed"] else None
        if h:
            it["flags"].append(h)


def address_hub(conn, office: dict) -> dict | None:
    """A registered office shared by a busy (50) or a thousand companies in the latest file."""
    if not office.get("in_latest"):
        return None
    n = db.rows(conn, "select count(distinct entity_key) as n from pub.company_addresses where in_latest and line_1 = %s "
                      "and coalesce(line_2, '') = %s and coalesce(postcode, '') = %s",
                (office.get("line_1"), office.get("line_2") or "", office.get("postcode") or ""))[0]["n"]
    if n >= SETTINGS["thousand_address"]:
        return flag("thousand-address", f"an address with a thousand companies: {n:,} companies have their registered office here; "
                                        f"a shared address here is no connection", {"companies": n})
    if n >= SETTINGS["busy_address"]:
        return flag("busy-address", f"a busy address: {n:,} companies have their registered office here", {"companies": n})
    return None


# ── the register's own rows on an entity ────────────────────────────────────

def roles_on(conn, ev: cat.View, e: dict, allowed: set, skipped: list) -> list:
    out = []
    for child, column, order in ROLES_ON.get(ev.name, ()):
        if child not in allowed:
            skipped.append(child)
            continue
        cv = cat.BY_NAME[child]
        total, got = rows_where(conn, child, column, e[ev.key_col], order)
        for r in got:
            out.append(item(cv, r, rows.title(ev, e), via=rows.ref_of(ev, str(e[ev.key_col]))))
        if total > len(got):
            out.append({"omitted": total - len(got), "view": child, "via": rows.ref_of(ev, str(e[ev.key_col]))})
    return out


def pointing_at(conn, ev: cat.View, e: dict, allowed: set, skipped: list) -> list:
    out = []
    for child, column, order in POINTING_AT.get(ev.name, ()):
        if child not in allowed:
            skipped.append(child)
            continue
        cv = cat.BY_NAME[child]
        total, got = rows_where(conn, child, column, e[ev.key_col], order)
        for r in got:
            out.append(item(cv, r, rows.title(ev, e), via=rows.ref_of(ev, str(e[ev.key_col]))))
        if total > len(got):
            out.append({"omitted": total - len(got), "view": child, "via": rows.ref_of(ev, str(e[ev.key_col]))})
    return out


def rows_where(conn, view: str, column: str, value, order: str) -> tuple:
    return rows.rows_where(conn, view, column, value, LIMITS["roles"], order)


# ── the walk ────────────────────────────────────────────────────────────────

def link_item(conn, l: dict, cache: dict, allowed: set, skipped: list, via: str = None) -> dict | None:
    hit = resolve(conn, l["other"], cache)
    if not hit:
        return {"ref": l["other"], "missing": True, "rule": l["rule"], "grade": l["grade"], "reason": l.get("reason"), "via": via or l["this"],
                "statement": f"{l['other']}: row not found in the published views (its key has moved or it was withdrawn)", "flags": [],
                "dates": {"undated": True, "text": rows.UNDATED}, "citation": {"view": "", "key": l["other"]}, "kind": "", "view": "",
                "register": rows.split_ref(l["other"])[0], "title": l["other"], "suppressed": False, "row": {}, "note": ""}
    v, r = hit
    if v.name not in allowed:
        skipped.append(v.name)
        return None
    ev, e = rows.entity_of(conn, v, r)
    it = item(v, r, rows.title(ev, e) if e else None, via=via or l["this"], rule=l["rule"], evidence=l.get("evidence"),
              watch=l.get("watch") or [], decision=l.get("decision"))
    if e:
        it["entity"] = item(ev, e)
    if l["grade"] == "near":
        near(it, l.get("reason") or "the rule that joined these rows grades the link near", l["rule"])
    return it


def walk(conn, ref: str, allowed: set, depth: int = 2) -> dict:
    """The walk from one row. `allowed`: the published views the template
    names. `depth`: 1 = the group and the entities it sits on; 2 = also the
    other rows on those entities (near)."""
    cache = {}
    hit = resolve(conn, ref, cache)
    if not hit:
        return {"found": False, "why": f"{ref}: no published row has this ref"}
    sv, sr = hit
    skipped = []
    out = {"found": True, "start": item(sv, sr), "settings": dict(SETTINGS), "limits": dict(LIMITS), "skipped": skipped,
           "members": [], "confirmed": [], "near": [], "entities": [], "roles": [], "pointing": [], "second": [], "hubs": []}
    if sv.name not in allowed:
        out["start_outside_template"] = True
    # 1. the group
    g = group_of(conn, ref) if sv.kind == "person" else {"built": links_built(conn), "why": "an organisation needs no group: its official number is the link",
                                                            "rows": [ref], "size": 1, "contested": False, "omitted": 0, "group_id": None, "settings": None}
    out["group"] = {k: g[k] for k in ("built", "why", "group_id", "contested", "settings", "size", "omitted")}
    member_refs = list(g["rows"])
    for mref in member_refs:
        mhit = resolve(conn, mref, cache)
        if not mhit:
            continue
        mv, mr = mhit
        if mv.name not in allowed:
            skipped.append(mv.name)
            continue
        ev, e = rows.entity_of(conn, mv, mr)
        it = item(mv, mr, rows.title(ev, e) if e else None, via=None if mref == ref else ref)
        if g["contested"] and mref != ref:
            near(it, NEAR_CONTESTED_GROUP)
        out["members"].append(it)
        if e:
            eit = item(ev, e, via=mref, hop=it["dates"])
            if it["grade"] == "near":
                near(eit, it["reason"])
            out["entities"].append(eit)
    # 2. the links, confirmed and near
    L = links_of(conn, member_refs)
    out["links_built"] = L["built"]
    out["links_omitted"] = L["omitted"]
    members = set(member_refs)
    for l in L["confirmed"]:
        it = link_item(conn, l, cache, allowed, skipped)
        if it:
            it["in_group"] = l["other"] in members
            out["confirmed"].append(it)
            if not it.get("missing") and it["kind"] == "organisation" and l["other"] not in members:
                out["entities"].append(dict(it, hop=it["dates"]))
    for l in L["near"]:
        it = link_item(conn, l, cache, allowed, skipped)
        if it:
            out["near"].append(it)
            if not it.get("missing") and it["kind"] == "organisation":
                out["entities"].append(dict(it, hop=it["dates"]))
    # an organisation start is its own entity
    if sv.kind == "organisation" and sv.name in allowed and sv.name in ROLES_ON:
        out["entities"].insert(0, item(sv, sr))
    # 3. each entity: the register's own rows on it, rows pointing at it, its own links (one step)
    seen_entities, expanded = set(), 0
    entities = []
    for eit in out["entities"]:
        if eit["ref"] in seen_entities:
            continue
        seen_entities.add(eit["ref"])
        entities.append(eit)
    out["entities"] = entities[:LIMITS["entities"]]
    out["entities_omitted"] = max(0, len(entities) - LIMITS["entities"])
    for eit in out["entities"]:
        ev = cat.BY_NAME[eit["view"]]
        e = eit["row"]
        if ev.name == "companies":
            office = [r for r in rows.rows_where(conn, "company_addresses", "entity_key", e["key"], 5, "started_on")[1] if r.get("in_latest")] \
                if "company_addresses" in allowed else []
            for o in office[:1]:
                h = address_hub(conn, o)
                if h:
                    eit["flags"].append(h)
        h = name_hub(eit["title"]) if not eit["suppressed"] else None
        if h:
            eit["flags"].append(h)
        if ev.name in EXPAND_ONLY_AS_START and eit["ref"] != ref:
            eit["context_only"] = True
            continue
        if expanded >= LIMITS["expand"]:
            eit["not_expanded"] = True
            continue
        expanded += 1
        through_near = eit["grade"] == "near"
        for it in roles_on(conn, ev, e, allowed, skipped):
            if "omitted" in it:
                out["roles"].append(it)
                continue
            if it["ref"] in members or it["ref"] == ref:
                continue
            if it["kind"] == "person" and sv.kind == "person":
                near(it, NEAR_THROUGH_PEOPLE)
            elif through_near:
                near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
            if it["view"] == "company_addresses":
                h = address_hub(conn, it["row"])
                if h:
                    it["flags"].append(h)
            (out["second"] if it["kind"] == "person" and sv.kind == "person" else out["roles"]).append(it)
        for it in pointing_at(conn, ev, e, allowed, skipped):
            if "omitted" not in it and through_near:
                near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
            out["pointing"].append(it)
        if eit["ref"] != ref and ev.kind == "organisation":
            EL = links_of(conn, [eit["ref"]])
            for l in EL["confirmed"] + EL["near"]:
                if l["other"] in members or l["other"] == ref:
                    continue
                it = link_item(conn, l, cache, allowed, skipped, via=eit["ref"])
                if not it:
                    continue
                if through_near and it["grade"] == "confirmed":
                    near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
                elif it["grade"] == "confirmed" and l["grade"] == "confirmed":
                    pass
                out["near" if it["grade"] == "near" else "confirmed"].append(it)
            out["links_omitted"] += EL["omitted"]
    if depth < 2:
        out["second"] = []
    # 4. hubs on every person met
    people = [it for k in ("members", "confirmed", "near", "second", "roles") for it in out[k] if it.get("kind") == "person" and "omitted" not in it]
    flag_people(conn, people)
    out["hubs"] = [{"ref": it["ref"], "title": it["title"], **f} for k in ("start", ) for it in [out["start"]] for f in it["flags"]] + \
                  [{"ref": it["ref"], "title": it["title"], **f} for k in ("members", "entities", "confirmed", "near", "roles", "second") for it in out[k]
                   if "omitted" not in it for f in it["flags"]]
    out["skipped"] = sorted(set(skipped))
    return out
