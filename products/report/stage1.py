"""The one report's first stage (step 9 tranche 6, ruling 157): the diagnostic
walk with no near link followed, and the confirmed web around the subject to a
measured depth.

What it does, on top of `walk.walk(..., near_links=False)`:

- **Hops.** From a person (or a filed row that takes a person's group), hop 1
  is the organisations the person's own rows sit on, current roles only; hop 2
  is the current people on those organisations. From an organisation, hop 1 is
  its current people (each with the rest of the person's confirmed group) and
  hop 2 is the other organisations those people sit on. The hop after the
  last is counted and said, never listed (`beyond_entities`, `beyond_people`).
- **Hubs.** An organisation with more than `HUB_PEOPLE` current people on it,
  or a person on more than `HUB_ENTITIES` organisations, is listed and flagged
  and not followed further. The subject's own record is always followed.
- **What is followed.** Confirmed identity groups (`pub.groups`), confirmed
  links to an organisation, and the register rows that sit on an organisation
  (`pub.names.entity_ref`) in FOLLOW_VIEWS. An insolvency appointee or a
  party's donor is listed by the walk and never followed here. A near link is
  never followed; the walk counts the ones it met (`near_set_aside`).
- **Grades.** The subject's own organisations are confirmed; anything past
  them is near by the design's default (a connection through more than one
  person), with the reason, never confirmed.

The depth and the hub limits are Arthur's question (docs/research/
step-9-stage1-depth.md, at the top): HOPS = 2 and 50/50 are the safest measured
option. Changing a constant is the whole change."""
from __future__ import annotations

from products.report import catalogue as cat
from products.report import db, rows, walk

HOPS = 3             # the hops listed (the next is counted, never listed); ruling 158, option B
HUB_PEOPLE = 50      # an organisation with more current people than this is listed, flagged and not followed
HUB_ENTITIES = 50    # a person on more organisations than this is listed, flagged and not followed
LIST_ROWS = 400      # the most rows the first stage adds to a report; the rest are counted (`omitted`)
LIST_ENTITIES = 200  # the most organisations it adds
CHUNK = 2000

FOLLOW_VIEWS = ("directors", "shareholders", "society_officers", "charity_officers", "limited_partnership_partners",
                "company_lookup_roles", "company_lookup_holdings")
ENTITY_VIEW = {"companies": "companies", "societies": "societies", "charities": "charities",
               "limited_partnerships": "limited_partnerships"}
HUB_TEXT_PEOPLE = "an organisation with more than {n} current people on it: listed, and the people on it not followed further"
HUB_TEXT_ENTITIES = "a person on more than {n} organisations: listed, and the organisations not followed further"
NEAR_STAGE_ORG = ("an organisation of {who}, a person on the subject: a connection through a person is the person's, listed near by the "
                  "design's default, never confirmed")


def is_entity_ref(ref: str) -> bool:
    reg, _, key = (ref or "").partition(":")
    return reg in ENTITY_VIEW and key.count("/") == 1


def current(view: str, r: dict) -> bool:
    """A role row still held: in the latest file with no end filed (directors), in the latest file (holders), current (partners,
    the business-number register's holdings), no end filed (the rest)."""
    if view == "directors":
        return walk.current_role(r)
    if view == "shareholders":
        return bool(r.get("in_latest", True))
    if view in ("limited_partnership_partners", "company_lookup_holdings"):
        return r.get("current") is not False and not r.get("ended_on")
    return not r.get("ended_on")


def _chunks(xs):
    xs = sorted(xs)
    for i in range(0, len(xs), CHUNK):
        yield xs[i:i + CHUNK]


def _q(conn, sql: str, xs, n: int = 1) -> list:
    out = []
    for c in _chunks(xs):
        out += db.rows(conn, sql, (c,) * n)
    return out


def _fetch(conn, refs) -> dict:
    """{ref: (view, row)} for role rows (by pub.names' view) and organisations (by register), in one query a view."""
    by_view = {}
    for x in _q(conn, "select ref, view from pub.names where ref = any(%s)", [r for r in refs if not is_entity_ref(r)]):
        by_view.setdefault(x["view"], []).append(x["ref"])
    for r in refs:
        if is_entity_ref(r):
            by_view.setdefault(ENTITY_VIEW[r.split(":", 1)[0]], []).append(r)
    out = {}
    for view, rs in by_view.items():
        v = cat.BY_NAME.get(view)
        if not v:
            continue
        keys = [rows.split_ref(r)[1] for r in rs]
        for row in _q(conn, f"select *, {v.key_col} as key from pub.{v.name} where {v.key_col} = any(%s)", keys):
            out[rows.ref_of(v, str(row["key"]))] = (v, row)
    return out


class Web:
    """The confirmed web from one start, hop by hop: counts first, rows fetched only for what is listed."""

    def __init__(self, conn):
        self.conn = conn
        self.view_of, self.entity_of, self.group = {}, {}, {}

    def names(self, refs):
        new = [r for r in refs if r not in self.view_of and not is_entity_ref(r)]
        for x in _q(self.conn, "select ref, view, entity_ref from pub.names where ref = any(%s)", new):
            self.view_of[x["ref"]], self.entity_of[x["ref"]] = x["view"], x["entity_ref"]
        for r in new:
            self.view_of.setdefault(r, None)

    def groups(self, refs) -> dict:
        """{row: group id} for refs, and {group id: [rows]} for the groups met."""
        new = [r for r in refs if r not in self.group]
        for x in _q(self.conn, "select row_key, group_id from pub.groups where row_key = any(%s)", new):
            self.group[x["row_key"]] = x["group_id"]
        for r in new:
            self.group.setdefault(r, None)
        gids = {self.group[r] for r in refs if self.group.get(r)}
        members = {}
        for x in _q(self.conn, "select row_key, group_id from pub.groups where group_id = any(%s)", gids):
            members.setdefault(x["group_id"], []).append(x["row_key"])
            self.group[x["row_key"]] = x["group_id"]
        return members

    def person(self, r) -> str:
        return self.group.get(r) or r

    def confirmed_entities(self, refs) -> dict:
        """{row: {organisation refs}} the confirmed links from the rows reach (an organisation link, an official number)."""
        out = {}
        for l in _q(self.conn, "select row_a, row_b from pub.links where grade = 'confirmed' and row_a = any(%s) union "
                               "select row_a, row_b from pub.links where grade = 'confirmed' and row_b = any(%s)", refs, 2):
            for this, other in ((l["row_a"], l["row_b"]), (l["row_b"], l["row_a"])):
                if this in refs and is_entity_ref(other):
                    out.setdefault(this, set()).add(other)
        return out

    def on(self, ents) -> dict:
        """{organisation: [rows on it in FOLLOW_VIEWS]}."""
        out = {}
        for c in _chunks(ents):
            for x in db.rows(self.conn, "select ref, view, entity_ref from pub.names where entity_ref = any(%s) and view = any(%s)",
                             (c, list(FOLLOW_VIEWS))):
                self.view_of[x["ref"]], self.entity_of[x["ref"]] = x["view"], x["entity_ref"]
                out.setdefault(x["entity_ref"], []).append(x["ref"])
        return out

    def current_only(self, refs) -> set:
        """The refs whose rows are current (a row the view does not carry is kept: it is not a role)."""
        got = _fetch(self.conn, refs)
        self.rows = getattr(self, "rows", {})
        self.rows.update(got)
        return {r for r in refs if r not in got or current(got[r][0].name, got[r][1])}


def closure(conn, start: str, own: list, hops: int = HOPS, hub_people: int = HUB_PEOPLE, hub_entities: int = HUB_ENTITIES) -> dict:
    """The confirmed web from `start` (whose own rows, the group, are `own`): {'levels', 'entities': {ref: hop}, 'people':
    {row: (hop, via organisation or officer row)}, 'hubs': [(ref, kind, n)], 'beyond_entities', 'beyond_people', 'cut'}.
    Counts and refs only; the rows listed are fetched by `items`."""
    W = Web(conn)
    ents, people, hubs, levels, through = {}, {}, [], [], {}
    beyond_entities = beyond_people = 0
    from_org = is_entity_ref(start)
    mine = set()

    def entities_of(rows_, hop, through=None):
        """The organisations the rows sit on, current roles only, a person on more than hub_entities not followed."""
        W.names(rows_)
        live = W.current_only([r for r in rows_ if W.view_of.get(r) in FOLLOW_VIEWS]) | {r for r in rows_ if W.view_of.get(r) not in FOLLOW_VIEWS}
        linked = W.confirmed_entities(set(rows_))
        per = {}
        for r in rows_:
            es = set(linked.get(r, ()))
            if r in live and W.view_of.get(r) in FOLLOW_VIEWS and is_entity_ref(W.entity_of.get(r) or ""):
                es.add(W.entity_of[r])
            for e in es:
                per.setdefault(W.person(r), {}).setdefault(e, r)
        out = {}
        for p, es in per.items():
            if len(es) > hub_entities and p not in mine:
                hubs.append((next(iter(es.values())), "person", len(es)))
                continue
            for e, r in es.items():
                out.setdefault(e, (through or {}).get(p) or r)
        return out

    def people_on(es, hop):
        on = W.on(es)
        live = W.current_only([r for rs in on.values() for r in rs])
        out = {}
        for e, rs in on.items():
            rs = [r for r in rs if r in live]
            if len(rs) > hub_people and e != start:
                hubs.append((e, "organisation", len(rs)))
                continue
            for r in rs:
                out.setdefault(r, e)
        return out

    # the frontier alternates: organisations, then the people on them, then their other organisations, and so on
    seen_rows = set(own)
    if from_org:
        ents[start] = 0
        frontier, kind = {start: start}, "entities"
    else:
        members = W.groups(own)
        mine = {W.person(r) for r in own}
        own = sorted(set(own) | {m for g in members.values() for m in g})
        seen_rows |= set(own)
        frontier, kind = {r: r for r in own}, "rows"
    officer_of = {}
    for hop in range(1, hops + 2):
        last = hop == hops + 1     # the hop after the last: counted, never listed
        if kind == "entities":
            on = people_on(sorted(e for e in frontier if e not in {h[0] for h in hubs}), hop)
            new = {r: e for r, e in on.items() if r not in seen_rows}
            if last:
                beyond_people = len({W.person(r) for r in new})
                beyond_entities = 0
                break
            members = W.groups(list(new))
            grown = {}
            for r, e in new.items():
                people[r] = (hop, e)
                if from_org and hop == 1:
                    officer_of.setdefault(W.person(r), r)
                for m in members.get(W.group.get(r), [r]):
                    grown.setdefault(m, r)
            seen_rows |= set(grown)
            levels.append({"hop": hop, "entities": 0, "people": len({W.person(r) for r in new})})
            frontier, kind = grown, "rows"
        else:
            got = entities_of(sorted(frontier), hop, officer_of)
            new = {e: (frontier.get(r) or r) for e, r in got.items() if e not in ents}
            if last:
                beyond_entities, beyond_people = len(new), 0
                break
            for e, r in new.items():
                ents[e] = hop
                through[e] = r
            levels.append({"hop": hop, "entities": len(new), "people": 0})
            frontier, kind = new, "entities"
        if not frontier:
            beyond_entities = beyond_people = 0
            break
    return _done(W, levels, ents, people, hubs, beyond_entities, beyond_people, through)


def _done(W, levels, ents, people, hubs, beyond_entities, beyond_people, through) -> dict:
    return {"levels": levels, "entities": ents, "people": people, "hubs": hubs, "through": through, "web": W,
            "beyond_entities": beyond_entities, "beyond_people": beyond_people, "cut": bool(beyond_entities or beyond_people)}


def items(conn, c: dict, start: str, taken: set, officer_titles: dict) -> tuple:
    """(items, omitted): the web's organisations and people the walk did not list, as report items, each marked `stage1`
    with its `stage_hop`; organisations first, to LIST_ENTITIES, then people, to LIST_ROWS in all."""
    want_e = [e for e, h in sorted(c["entities"].items(), key=lambda kv: (kv[1], kv[0])) if e not in taken and e != start]
    want_p = [r for r, (h, _) in sorted(c["people"].items(), key=lambda kv: (kv[1][0], kv[0])) if r not in taken]
    omitted = max(0, len(want_e) - LIST_ENTITIES)
    want_e = want_e[:LIST_ENTITIES]
    room = max(0, LIST_ROWS - len(want_e))
    omitted += max(0, len(want_p) - room)
    want_p = want_p[:room]
    have = dict(getattr(c["web"], "rows", {}))
    need = [r for r in want_e + want_p + [e for _, e in (c["people"][r] for r in want_p)] if r not in have]
    have.update(_fetch(conn, need))
    hub_of = {ref: (kind, n) for ref, kind, n in c["hubs"]}
    out = []
    for e in want_e:
        if e not in have:
            continue
        v, r = have[e]
        it = walk.item(v, r, stage1=True, stage_hop=c["entities"][e])
        if c["entities"][e] >= 2:
            off = c["through"].get(e)
            it.update(via=off, through=off, depth=1)
            walk.near(it, NEAR_STAGE_ORG.format(who=officer_titles.get(off) or "an officer"), "stage1")
        _hub(it, hub_of)
        out.append(it)
    for p in want_p:
        if p not in have:
            continue
        hop, e = c["people"][p]
        v, r = have[p]
        ev = have.get(e)
        it = walk.item(v, r, rows.title(*ev) if ev else None, via=e, stage1=True, stage_hop=hop,
                       person=c["web"].group.get(p))
        if it["kind"] == "person" and hop >= 2:
            walk.near(it, walk.NEAR_THROUGH_PEOPLE, "stage1")
        _hub(it, hub_of)
        out.append(it)
    return out, omitted


def _hub(it, hub_of):
    h = hub_of.get(it["ref"])
    if h:
        kind, n = h
        it["flags"].append({"kind": "stage-hub", "text": (HUB_TEXT_PEOPLE if kind == "organisation" else HUB_TEXT_ENTITIES).format(
            n=HUB_PEOPLE if kind == "organisation" else HUB_ENTITIES) + f" ({n})", "evidence": {"count": n}})


def walk1(conn, ref: str, allowed: set, depth: int = 2, buckets=None, chain_depth: int = 0) -> dict:
    """The walk for the one report's first stage: the diagnostic walk with no near link, and the confirmed web in the bucket
    `stage1`, its counts in `stage1_stats` (copied to report['walk']['stage1'])."""
    w = walk.walk(conn, ref, allowed, depth=depth, buckets=buckets, chain_depth=chain_depth, near_links=False)
    if not w.get("found"):
        return w
    own = [ref] + [m["ref"] for m in w["members"] if m["grade"] == "confirmed"]
    c = closure(conn, ref, own)
    taken = {ref} | {it["ref"] for b in walk.BUCKETS for it in w.get(b, []) if "ref" in it} | {e["ref"] for e in w["entities"]}
    titles = {it["ref"]: it["title"] for it in w.get("roles", []) if "ref" in it}
    listed, omitted = items(conn, c, ref, taken, titles)
    w["stage1"] = [it for it in listed if it["view"] in allowed]
    for it in w["stage1"]:
        for f in it["flags"]:
            w["hubs"].append({"ref": it["ref"], "title": it["title"], **f})
    w["stage1_stats"] = {"stage": 1, "depth": HOPS, "hub_people": HUB_PEOPLE, "hub_entities": HUB_ENTITIES,
                         "levels": c["levels"], "cut": c["cut"], "beyond_entities": c["beyond_entities"],
                         "beyond_people": c["beyond_people"], "hubs_not_expanded": len(c["hubs"]), "omitted": omitted,
                         "listed": len(w["stage1"]), "near_set_aside": w.get("near_set_aside", 0),
                         "holders_by_name_set_aside": (w.get("chain_stats") or {}).get("by_name_set_aside", 0)}
    return w
