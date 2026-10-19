"""The links, groups and decisions as the board shows them, read from the
views links/ publishes in `pub` (plan step 4.9: the board reads published
tables, links and groups only). Until those views exist every pane says so
plainly: no link is made by looking, and none is guessed here.

A row is named to the links tables by its register and stable key,
`<register>:<key>` (links/tables.sql: 'a register row's stable key,
schema-qualified'). That form is the links module's to settle; the board
reads whatever `pub.links` carries and maps it back by register."""
from __future__ import annotations

from products.board import catalogue as cat
from products.board import db

NOT_BUILT = "no links built yet: links/ has published nothing (plan step 4.2 builds them)"


def ref(v: cat.View, key: str) -> str:
    return f"{v.register}:{key}"


def split_ref(r: str) -> tuple:
    register, _, key = r.partition(":")
    return register, key


def view_for(conn, register: str, key: str):
    """The view in that register whose row has this key, or None."""
    for v in cat.views_of(register):
        cur = conn.execute(f"select 1 from pub.{v.name} where {v.key_col} = %s limit 1", (key,))
        if cur.fetchone():
            return v
    return None


def built(conn) -> bool:
    return db.has_relation(conn, "pub", "links")


def links_of(conn, r: str) -> dict:
    """{'built': bool, 'why': str, 'confirmed': [...], 'near': [...]}; each
    link: other (ref), register, rule, evidence, reason, decisions (list)."""
    if not built(conn):
        return {"built": False, "why": NOT_BUILT, "confirmed": [], "near": []}
    found = db.rows(conn, "select * from pub.links where row_a = %s or row_b = %s order by grade, rule, row_a, row_b limit 500", (r, r))
    decisions = {}
    if db.has_relation(conn, "pub", "decisions"):
        for d in db.rows(conn, "select * from pub.decisions where row_a = %s or row_b = %s order by made_at", (r, r)):
            other = d["row_b"] if d["row_a"] == r else d["row_a"]
            decisions.setdefault(other, []).append(d)
    out = {"built": True, "why": "", "confirmed": [], "near": []}
    for l in found:
        other = l["row_b"] if l["row_a"] == r else l["row_a"]
        register, _ = split_ref(other)
        out[l["grade"] if l["grade"] in ("confirmed", "near") else "near"].append({
            "other": other, "register": register, "rule": l["rule"], "evidence": l.get("evidence"),
            "reason": l.get("reason"), "decisions": decisions.get(other, [])})
    return out


def group_of(conn, r: str) -> dict:
    """The group this row belongs to, as links/ built it: {'built', 'why',
    'group_id', 'contested', 'rows': [refs]}."""
    if not db.has_relation(conn, "pub", "groups"):
        return {"built": False, "why": NOT_BUILT, "rows": []}
    mine = db.rows(conn, "select * from pub.groups where row_key = %s", (r,))
    if not mine:
        return {"built": True, "why": "this row is in no group: no confirmed link reaches it", "rows": [r], "contested": False}
    g = mine[0]
    rows = db.rows(conn, "select row_key from pub.groups where group_id = %s order by row_key limit 1000", (g["group_id"],))
    return {"built": True, "why": "", "group_id": g["group_id"], "contested": bool(g.get("contested")),
            "settings": g.get("settings"), "rows": [x["row_key"] for x in rows]}
