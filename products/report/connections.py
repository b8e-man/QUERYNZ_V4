"""The one report's connections, by type (Arthur, 10 November 2026; rulings 158 and 159): the kinds of row the walk
lists, named in plain words, each shown or not and with the variables its type declares, and the base configuration a
report starts with by the kind of its subject. Declared in `connections.toml` beside this file; this module reads it.

A setting changes what is followed, not only what is shown, so the report is rebuilt with it:

- **Off.** A type that is off is neither listed nor followed: its rows leave every bucket of the walk, and so does
  every row reached through one of them (an item whose `via` or `through` names a row that left), counted per type.
  The first stage's web (stage1.closure) is told too, so it does not walk on from those rows.
- **Roles.** `when`: current only (another person's ended role is not listed), past too and listed (the walk as it
  was: listed, followed only while current), past too and followed (the first stage walks on from an ended role).
  `since`: a role that ended before the date is not listed and not followed. The subject's own rows always stay.
- **From it.** `follow` no: the rows are listed, and nothing reached through one of them is (a trustee company's
  directors listed, their other directorships not followed).
- **Donations.** `order` (size or recency), `top` (how many), `years` (over what period): the donations a report lists
  are the top so many by the order within the period; the rest are counted. A party's own donations (the rows its
  returns file under its party key) are read for a party subject, which the walk alone does not reach. A donation's
  own amount is a filter the reader chose (Arthur's base for a party), never a prior on a person.

The subject is never removed, nor a row of its own group. Hubs said on the result (ruling 158) come from the first
stage (stage1.hub_lines) and from the base configuration's `hub` line here, with the count and the reason."""
from __future__ import annotations

import datetime as dt
import functools
import os
import re
import tomllib

from products.report import catalogue as cat
from products.report import db, rows, stage1, walk

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "connections.toml")
ROLE_VARS = ("when", "since", "follow")
QUERY = "c"           # the page's marker: the pane's form was sent, so a type with no tick is off
PARTY_READ = 200      # the most donation rows a party subject's query brings back before its own `top`
PRUNED_BUCKETS = tuple(b for b in walk.BUCKETS if b != "members") + ("entities",)


@functools.lru_cache(maxsize=None)
def config(path: str = PATH) -> dict:
    """{'variables': {name: {...}}, 'types': [...], 'by_view': {view: type key}, 'base': [...]}; refused when a type names
    a view the catalogue does not know, a variable not declared, or a view twice."""
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    variables = raw.get("variables", {})
    for name, v in variables.items():
        if v["default"] not in {c[0] for c in v["choices"]}:
            raise ValueError(f"connections.toml: variable {name}'s default is not one of its choices")
    by_view, types = {}, []
    for t in raw.get("types", []):
        for view in t["views"]:
            if view not in cat.BY_NAME:
                raise ValueError(f"connections.toml: type {t['key']} names {view}, a view the catalogue does not know")
            if view in by_view:
                raise ValueError(f"connections.toml: {view} is in two types ({by_view[view]}, {t['key']})")
            by_view[view] = t["key"]
        for name in t.get("variables", []):
            if name not in variables:
                raise ValueError(f"connections.toml: type {t['key']} names {name}, a variable not declared")
        types.append({"key": t["key"], "words": t["words"], "views": tuple(t["views"]), "variables": tuple(t.get("variables", []))})
    keys = {t["key"] for t in types}
    for b in raw.get("base", []):
        for k in b.get("set", {}):
            tk, _, var = k.partition(".")
            if tk not in keys or (var and var not in next(t for t in types if t["key"] == tk)["variables"]):
                raise ValueError(f"connections.toml: base {b['subject']} sets {k}, which no type declares")
    return {"variables": variables, "types": types, "by_view": by_view, "base": raw.get("base", [])}


def register_type(register: str) -> str:
    return "register:" + register


def type_of(it: dict) -> str:
    """The connection type of a walk item (or an `omitted` count): its view's type, else its register's."""
    v = it.get("view")
    t = config()["by_view"].get(v)
    if t:
        return t
    cv = cat.BY_NAME.get(v)
    return register_type(cv.register if cv else "unknown")


def words_of(key: str) -> str:
    for t in config()["types"]:
        if t["key"] == key:
            return t["words"]
    if key.startswith("register:"):
        return cat.REGISTER_NAME.get(key.split(":", 1)[1], key.split(":", 1)[1])
    return key


def variables_of(key: str) -> tuple:
    for t in config()["types"]:
        if t["key"] == key:
            return t["variables"]
    return ()


# ── the subject's kind and the base configuration ──────────────────────────

def subject_kind(view: str, ref: str, title: str) -> dict | None:
    """The first `[[base]]` the subject matches, or None (every type as before)."""
    frag = ref.partition("#")[2]
    for b in config()["base"]:
        if view not in b.get("views", ()):
            continue
        if frag and b.get("fragment") and frag != b["fragment"]:
            continue
        if b.get("name") and not re.search(rf"\b({b['name']})\b", cat.fold(title or ""), re.I):
            continue
        return b
    return None


def defaults() -> dict:
    """{type: {'show': True, variable: its default}} for every declared type."""
    v = config()["variables"]
    return {t["key"]: {"show": True, **{n: v[n]["default"] for n in t["variables"]}} for t in config()["types"]}


def base(kind: dict | None) -> dict:
    """The settings a report on a subject of this kind starts with."""
    out = defaults()
    for k, value in ((kind or {}).get("set") or {}).items():
        tk, _, var = k.partition(".")
        if var:
            out[tk][var] = str(value)
        else:
            out[tk]["show"] = str(value) != "off"
    return out


def get(settings: dict, key: str) -> dict:
    """A type's settings; a register's type (no declared variables) is shown unless the settings say otherwise."""
    return settings.get(key) or {"show": True}


def from_query(qs: dict, kind: dict | None) -> dict:
    """The settings from the page's address on top of the base: `c.<type>.<variable>=value` for a variable (a value not
    among its choices is ignored), and, once the pane's form was sent (`c=1`), a type with no `c.<type>=on` is off.
    A register's type (`c.register:<name>`) is ticked like any other."""
    one = {k: (v[0] if isinstance(v, (list, tuple)) else v) for k, v in (qs or {}).items()}
    out = base(kind)
    variables = config()["variables"]
    sent = one.get(QUERY) == "1"
    for k, v in one.items():
        if not k.startswith(QUERY + "."):
            continue
        tk, _, var = k[len(QUERY) + 1:].partition(".")
        if var:
            if tk in out and var in out[tk] and var in variables and v in {c[0] for c in variables[var]["choices"]}:
                out[tk][var] = v
        elif tk.startswith("register:"):
            out.setdefault(tk, {"show": True})
    if sent:
        for tk in out:
            out[tk]["show"] = one.get(f"{QUERY}.{tk}") == "on"
        for k in one:   # a register's type the form ticked
            if k.startswith(QUERY + ".register:") and one[k] == "on":
                out[k[len(QUERY) + 1:]] = {"show": True}
        out["_sent"] = True
    return out


def to_query(settings: dict) -> list:
    """The settings as the page's address carries them (every type, so the address reopens the report as it was)."""
    out = [(QUERY, "1")]
    for tk, s in settings.items():
        if tk.startswith("_"):
            continue
        if s.get("show", True):
            out.append((f"{QUERY}.{tk}", "on"))
        for var, value in s.items():
            if var != "show":
                out.append((f"{QUERY}.{tk}.{var}", value))
    return out


def shown(settings: dict, key: str) -> bool:
    s = settings.get(key)
    if s is None:   # a register's type the form did not tick, once it was sent
        return not settings.get("_sent")
    return s.get("show", True)


# ── what the walk is told ──────────────────────────────────────────────────

def _since_cutoff(value: str, today: dt.date) -> dt.date | None:
    if not value or value == "any":
        return None
    return dt.date(today.year - int(value), today.month, min(today.day, 28))


def ended_on(view: str, r: dict) -> dt.date | None:
    v = cat.BY_NAME.get(view)
    d = rows.as_date(r.get(v.end)) if v and v.end else None
    return d or rows.as_date(r.get("ended_on")) or rows.as_date(r.get("vacated_on"))


def role_keeps(settings: dict, today: dt.date | None = None):
    """(view, row) -> bool: whether the first stage walks on from a role row, by the role's type's `when` and `since`."""
    today = today or dt.date.today()

    def keep(view: str, r: dict) -> bool:
        s = get(settings, config()["by_view"].get(view, ""))
        if s.get("when") != "followed" and not stage1.current(view, r):
            return False
        cut = _since_cutoff(s.get("since", "any"), today)
        end = ended_on(view, r)
        return not (cut and end and end < cut)
    return keep


def views_where(settings: dict, test) -> set:
    return {v for t in config()["types"] for v in t["views"] if test(get(settings, t["key"]))}


def hidden_views(settings: dict) -> set:
    out = views_where(settings, lambda s: not s.get("show", True))
    for view, v in cat.BY_NAME.items():
        if view not in config()["by_view"] and not shown(settings, register_type(v.register)):
            out.add(view)
    return out


def stop_views(settings: dict) -> set:
    """Views whose rows are listed and not walked on from (`follow` no), and the hidden ones."""
    return views_where(settings, lambda s: s.get("follow") == "no") | hidden_views(settings)


# ── after the walk ─────────────────────────────────────────────────────────

def _year_of(it: dict) -> int | None:
    d = it.get("dates") or {}
    for k in ("on", "start", "published", "filed"):
        x = d.get(k)
        if isinstance(x, dt.date):
            return x.year
    y = d.get("year") or (it.get("row") or {}).get("year")
    return int(y) if str(y or "").isdigit() else None


def _when(it: dict) -> tuple:
    d = it.get("dates") or {}
    for k in ("on", "start", "published", "filed"):
        x = d.get(k)
        if isinstance(x, dt.date):
            return (x.year, x.toordinal())
    y = _year_of(it)
    return (y or 0, 0)


def _amount(it: dict) -> float:
    try:
        return float((it.get("row") or {}).get("amount") or 0)
    except (TypeError, ValueError):
        return 0.0


def donation_keep(items: list, s: dict, today: dt.date) -> tuple:
    """(kept, set aside) of donation items by the type's `years`, `order` and `top`."""
    years = s.get("years", "all")
    inside = [it for it in items if years == "all" or (_year_of(it) or 0) >= today.year - int(years)]
    out = [it for it in items if it not in inside]
    def when(it):
        y, d = _when(it)
        return (-y, -d)
    if s.get("order") == "recency":   # ties: the larger, then the ref, as the party's own query orders them
        inside.sort(key=lambda it: (when(it), -_amount(it), it["ref"]))
    else:
        inside.sort(key=lambda it: (-_amount(it), when(it), it["ref"]))
    top = s.get("top", "all")
    if top != "all":
        out += inside[int(top):]
        inside = inside[:int(top)]
    return inside, out


def kind_ranked(settings: dict) -> bool:
    """True when the donations' order differs from the base's, so it is the order they are listed in."""
    return get(settings, "donation").get("order") != config()["variables"]["order"]["default"]


def _views_of_refs(conn, refs) -> dict:
    refs = sorted(r for r in refs if r)
    if not refs or conn is None:
        return {}
    return {x["ref"]: x["view"] for x in db.rows(conn, "select ref, view from pub.names where ref = any(%s)", (refs,))}


def prune(w: dict, settings: dict, conn=None, today: dt.date | None = None) -> dict:
    """Takes out of the walk's buckets every row the settings leave out, and every row reached through one (`via`,
    `through`); counts them per type in w['connections']['set_aside']. Returns the counts."""
    today = today or dt.date.today()
    start = w["start"]["ref"]
    keep_own = {start} | {m["ref"] for m in w.get("members", [])}
    by_view = config()["by_view"]
    hidden = hidden_views(settings)
    keep_role = role_keeps(settings, today)
    items = [(b, it) for b in PRUNED_BUCKETS for it in w.get(b, [])]
    view_of = {it["ref"]: it["view"] for _, it in items if "ref" in it}
    view_of.update(_views_of_refs(conn, {it.get(k) for _, it in items for k in ("via", "through")} - set(view_of) - keep_own))
    stops = stop_views(settings)
    gone, why = set(), {}

    def leaves(it: dict) -> bool:
        if "omitted" in it:
            return it["view"] in hidden or it.get("via") in gone
        ref = it.get("ref")
        if ref is None:   # a chain's note: it says the chain goes on, and stays with it
            return it.get("via") in gone
        if ref in keep_own:
            return False
        view = it["view"]
        if view in hidden:
            return True
        tk = by_view.get(view)
        if tk and "when" in variables_of(tk) and it.get("row") is not None:
            s = get(settings, tk)
            if s.get("when") == "current" and not stage1.current(view, it["row"]):
                return True
            cut = _since_cutoff(s.get("since", "any"), today)
            end = ended_on(view, it["row"])
            if cut and end and end < cut:
                return True
        for k in ("via", "through"):
            x = it.get(k)
            if not x or x in keep_own:
                continue
            if x in gone or view_of.get(x) in stops:
                return True
        return False

    changed = True
    while changed:
        changed = False
        for _, it in items:
            key = id(it)
            if key in why:
                continue
            if leaves(it):
                why[key] = type_of(it)
                if "ref" in it:
                    gone.add(it["ref"])
                changed = True
    # an item listed in two buckets leaves from both
    counts = {}
    for b in PRUNED_BUCKETS:
        kept = []
        for it in w.get(b, []):
            if id(it) in why or ("ref" in it and it["ref"] in gone and it["ref"] not in keep_own):
                tk = type_of(it)
                counts[tk] = counts.get(tk, 0) + (it["omitted"] if "omitted" in it else 1)
            else:
                kept.append(it)
        w[b] = kept
    # donations: the period, the order and the top N, over every bucket at once
    s = get(settings, "donation")
    dviews = {v for t in config()["types"] if t["key"] == "donation" for v in t["views"]}
    don = [it for b in PRUNED_BUCKETS for it in w.get(b, []) if "ref" in it and it["view"] in dviews and it["ref"] not in keep_own]
    seen, uniq = set(), []
    for it in don:
        if it["ref"] not in seen:
            seen.add(it["ref"])
            uniq.append(it)
    kept, out = donation_keep(uniq, s, today)
    if s.get("top", "all") != "all" or kind_ranked(settings):
        for i, it in enumerate(kept, 1):   # the order chosen is the order listed (build._sort_key)
            for b in PRUNED_BUCKETS:
                for x in w.get(b, []):
                    if x.get("ref") == it["ref"]:
                        x["rank"] = i
    out_refs = {it["ref"] for it in out}
    if out_refs:
        for b in PRUNED_BUCKETS:
            w[b] = [it for it in w.get(b, []) if "ref" not in it or it["ref"] not in out_refs]
        counts["donation"] = counts.get("donation", 0) + len(out_refs)
    w.setdefault("connections", {})["set_aside"] = counts
    return counts


# ── the subject's own reaches the base configuration asks for ─────────────────

def party_donations(conn, w: dict, settings: dict, today: dt.date | None = None) -> dict:
    """A party subject's own donations: the rows its returns file under its party key (a return replaced by an amendment
    left out: never summed), within the period, by the order, to the top N, as walk items in `roles` via the party.
    Returns {'total', 'in_period', 'listed'}."""
    today = today or dt.date.today()
    s = get(settings, "donation")
    sv = cat.BY_NAME.get(w["start"]["view"])
    key = (w["start"].get("row") or {}).get(sv.key_col) if sv else None
    if not key:
        return {"total": 0, "in_period": 0, "listed": 0}
    v = cat.BY_NAME["party_return_donors"]
    years = s.get("years", "all")
    since = 0 if years == "all" else today.year - int(years)
    counted = db.rows(conn, "select count(*) as n, count(*) filter (where year >= %s) as p from pub.party_return_donors "
                            "where party_key = %s and replaced_by is null", (since, key))[0]
    if not shown(settings, "donation"):
        return {"total": counted["n"], "in_period": counted["p"], "listed": 0, "off": True}
    order = "year desc, amount desc nulls last" if s.get("order") == "recency" else "amount desc nulls last, year desc"   # then the key
    top = PARTY_READ if s.get("top", "all") == "all" else min(int(s["top"]), PARTY_READ)
    got = db.rows(conn, f"select *, {v.key_col} as key from pub.party_return_donors where party_key = %s and replaced_by is null "
                        f"and year >= %s order by {order}, {v.key_col} limit %s", (key, since, top))
    title = w["start"]["title"]
    have = {it["ref"] for b in PRUNED_BUCKETS for it in w.get(b, []) if "ref" in it}
    added = 0
    for r in got:
        it = walk.item(v, r, title, via=w["start"]["ref"])
        if it["ref"] in have:
            continue
        w["roles"].append(it)
        added += 1
    return {"total": counted["n"], "in_period": counted["p"], "listed": added}


def _choice_words(var: str, value: str) -> str:
    for k, words in config()["variables"][var]["choices"]:
        if k == value:
            return words
    return value


def base_hub_line(conn, w: dict, kind: dict, settings: dict, reached: dict, ref: str = "") -> dict | None:
    """The line the base configuration's `hub` asks for, with its count."""
    if not kind or not kind.get("hub"):
        return None
    s = w["start"]
    n = 0
    if kind["subject"] == "party":
        n = reached.get("total", 0)
    elif kind["subject"] == "liquidator":
        n = walk.group_of(conn, ref or s["ref"]).get("size", 1)
    elif kind["subject"] == "trustee":
        people = [it["ref"] for it in w.get("roles", []) if it.get("view") == "directors" and it.get("via") == s["ref"]]
        counts = walk.role_counts(conn, people)
        groups = {}
        for ref, (gid, nd, _) in counts.items():
            groups[gid or ref] = nd
        n = sum(groups.values())
    d = get(settings, "donation")
    text = (kind.get("hub_off") if reached.get("off") and kind.get("hub_off") else kind["hub"]).format(n=f"{n:,}", p=f"{reached.get('in_period', 0):,}", top=d.get("top", "all"), order=d.get("order", "size"),
                              years=_choice_words("years", d.get("years", "all")))
    out = {"ref": s["ref"], "title": s["title"], "kind": "base-" + kind["subject"], "count": n, "text": "a hub: " + text,
           "subject": True}
    if kind.get("gap"):
        out["gap"] = kind["gap"]
    return out


# ── the walker the builder runs ────────────────────────────────────────────

def walker(settings: dict, kind: dict | None, stage: int = 1, today: dt.date | None = None):
    """walk.walk's signature: the walk for the template's stage, told the settings, then pruned, then the base
    configuration's reaches and hub line added; w['connections'] carries what the pane shows."""
    def run(conn, ref, allowed, depth=2, buckets=None, chain_depth=0):
        if stage == 1:
            w = stage1.walk1(conn, ref, allowed, depth=depth, buckets=buckets, chain_depth=chain_depth, settings=settings)
        else:
            w = walk.walk(conn, ref, allowed, depth=depth, buckets=buckets, chain_depth=chain_depth)
        if not w.get("found"):
            return w
        reached = party_donations(conn, w, settings, today) if kind and kind["subject"] == "party" else {}
        counts = prune(w, settings, conn, today)
        if reached:   # the party's donations its query did not bring back are set aside too
            counts["donation"] = counts.get("donation", 0) + max(0, reached["total"] - reached["listed"])
        line = base_hub_line(conn, w, kind, settings, reached, ref)
        w.setdefault("hub_lines", [])
        if line:
            w["hub_lines"].insert(0, line)
        w["connections"].update(kind=(kind or {}).get("subject"), kind_words=(kind or {}).get("words"), settings=settings,
                                party=reached or None)
        return w
    return run


def settings_for(conn, ref: str, qs: dict | None) -> tuple:
    """(kind, settings) for a report on `ref` from the page's address."""
    hit = walk.resolve(conn, ref, {})
    if not hit:
        return None, base(None)
    v, r = hit
    kind = subject_kind(v.name, ref, rows.title(v, r))
    if kind and kind.get("min_directorships") and most_directorships(conn, r.get(v.key_col)) <= kind["min_directorships"]:
        kind = None
    return kind, from_query(qs or {}, kind)


def most_directorships(conn, company_key) -> int:
    """The most directorships a current director of the company holds, counted on the director's group."""
    dv = cat.BY_NAME["directors"]
    got = db.rows(conn, f"select {dv.key_col} as key from pub.directors where entity_key = %s and coalesce(in_latest, true) and ended_on is null "
                        f"limit 50", (company_key,))
    counts = walk.role_counts(conn, [rows.ref_of(dv, str(x["key"])) for x in got])
    return max((n for _, n, _ in counts.values()), default=0)


# ── what the pane shows ────────────────────────────────────────────────────

def pane_rows(report: dict) -> list:
    """[{'key', 'words', 'listed', 'set_aside', 'show', 'variables': [(name, words, value, choices)]}] in the declared
    order, then the registers' types: every type the report listed or set aside, and every declared type with variables
    the subject's base sets."""
    con = report.get("connections") or {}
    settings = con.get("settings") or defaults()
    listed = {}
    for sec in report.get("sections", []):
        for it in sec["items"]:
            if it.get("ref") == (report.get("subject") or {}).get("ref"):
                continue
            tk = type_of(it)
            listed[tk] = listed.get(tk, 0) + 1
    aside = con.get("set_aside") or {}
    declared = [t["key"] for t in config()["types"]]
    keys = [k for k in declared if listed.get(k) or aside.get(k) or not shown(settings, k)
            or any(get(settings, k).get(var) != config()["variables"][var]["default"] for var in variables_of(k))]
    keys += sorted({k for k in list(listed) + list(aside) if k not in declared})
    keys += sorted(k for k in settings if k.startswith("register:") and k not in keys)
    variables = config()["variables"]
    out = []
    for k in keys:
        s = get(settings, k)
        out.append({"key": k, "words": words_of(k), "listed": listed.get(k, 0), "set_aside": aside.get(k, 0), "show": shown(settings, k),
                    "variables": [(var, variables[var]["words"], s.get(var, variables[var]["default"]), variables[var]["choices"])
                                  for var in variables_of(k)]})
    return out
