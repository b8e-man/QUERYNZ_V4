"""Hubs flagged on a line: a professional director (a person whose group
holds `hub_roles` directorships or more), a nominee or trustee holder, the
Crown or a Crown body by name, and a company whose registered office is
shared by a thousand companies. A hub is still listed; the flag tells the
reader why what it joins means little on its own. Counted in a few queries
per batch of lines, never one per line; the busy addresses are read once
per run. Reads `pub.*` only."""
from __future__ import annotations

import re

from products.scan import views as cat

SETTINGS = {"hub_roles": 50, "thousand_address": 1000}
NOMINEE = re.compile(r"\b(nominees?|trustees?|custodians?|custodial)\b", re.I)
CROWN = re.compile(r"\b(her majesty|his majesty|the crown|the sovereign|minister (of|for)|crown entity)\b", re.I)
PERSON_HUB_VIEWS = frozenset({"directors", "shareholders", "society_officers", "charity_officers"})
CHUNK = 5000


def _rows(conn, sql: str, params=()) -> list:
    cur = conn.execute(sql, params)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur]


def name_hub(name: str) -> dict | None:
    if not name or name == "name suppressed":
        return None
    if CROWN.search(name):
        return {"kind": "crown", "text": "the Crown: a hub that joins thousands of rows; a connection through it means little on its own"}
    if NOMINEE.search(name):
        return {"kind": "nominee", "text": "a nominee or trustee holder: it holds as the register states, for others; never shown as an owner"}
    return None


def busy_addresses(conn) -> set:
    """Every registered office shared by `thousand_address` companies or more in the latest file, as (line_1, line_2, postcode)."""
    got = _rows(conn, "select line_1, coalesce(line_2, '') as line_2, coalesce(postcode, '') as postcode from pub.company_addresses "
                      "where in_latest group by 1, 2, 3 having count(distinct entity_key) >= %s", (SETTINGS["thousand_address"],))
    return {(x["line_1"], x["line_2"], x["postcode"]) for x in got}


def directorships_by_group(conn, refs: list) -> dict:
    """{ref: (group_id, directorships in the group)} for person refs, two queries per chunk."""
    out = {}
    refs = sorted(set(refs))
    for i in range(0, len(refs), CHUNK):
        chunk = refs[i:i + CHUNK]
        mine = _rows(conn, "select row_key, group_id from pub.groups where row_key = any(%s)", (chunk,))
        groups = sorted({x["group_id"] for x in mine})
        counts = {}
        for j in range(0, len(groups), CHUNK):
            for x in _rows(conn, "select g.group_id, count(*) as n from pub.groups g join pub.names n on n.ref = g.row_key "
                                 "where g.group_id = any(%s) and n.view = 'directors' group by 1", (groups[j:j + CHUNK],)):
                counts[x["group_id"]] = x["n"]
        for x in mine:
            out[x["row_key"]] = (x["group_id"], counts.get(x["group_id"], 0))
    return out


def offices_of(conn, keys: list) -> dict:
    """{company key: (line_1, line_2, postcode)} in the latest file."""
    out = {}
    keys = sorted(set(keys))
    for i in range(0, len(keys), CHUNK):
        for x in _rows(conn, "select entity_key, line_1, coalesce(line_2, '') as line_2, coalesce(postcode, '') as postcode "
                             "from pub.company_addresses where in_latest and entity_key = any(%s)", (keys[i:i + CHUNK],)):
            out[x["entity_key"]] = (x["line_1"], x["line_2"], x["postcode"])
    return out


def flag(conn, lines: list, busy: set) -> int:
    """Adds hubs to each line's `hubs` ({step, kind, text}); returns how many lines carry one."""
    people = [s["ref"] for ln in lines for s in ln["steps"] if s["view"] in PERSON_HUB_VIEWS and not s["suppressed"] and not s.get("absent")]
    companies = [s["ref"].split(":", 1)[1] for ln in lines for s in ln["steps"] if s["view"] == "companies" and not s.get("absent")]
    roles = directorships_by_group(conn, people) if people else {}
    offices = offices_of(conn, companies) if (companies and busy) else {}
    n = 0
    for ln in lines:
        for s in ln["steps"]:
            if s.get("absent"):
                continue
            v = cat.BY_NAME[s["view"]]
            if v.kind == "organisation" or s["view"] == "shareholders":
                h = name_hub(s["title"])
                if h:
                    ln["hubs"].append({"step": s["label"], **h})
            if s["view"] in PERSON_HUB_VIEWS and s["ref"] in roles:
                gid, k = roles[s["ref"]]
                if k >= SETTINGS["hub_roles"]:
                    ln["hubs"].append({"step": s["label"], "kind": "professional-director",
                                       "text": f"a professional director: this person's group holds {k:,} directorships; a shared board with them joins little"})
            if s["view"] == "companies" and offices.get(s["ref"].split(":", 1)[1]) in busy:
                ln["hubs"].append({"step": s["label"], "kind": "thousand-address",
                                   "text": "a registered office shared by a thousand companies or more; a shared address here is no connection"})
        if ln["hubs"]:
            n += 1
    return n
