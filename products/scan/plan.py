"""A scan's steps compiled to one query over `pub`, under the chains
setting. Each step is an alias `s<i>`; the select list carries, for every
step, the columns the catalogue reads and the template's own, named
`s<i>__<column>`, and for a person or link step the grade columns the line
builder reads: `s<i>__contested` and `s<i>__group` (a group step),
`s<i>__grade`, `s<i>__reason`, `s<i>__rule`, `s<i>__decision`, `s<i>__link`
(a link step), `s<i>__by` and `s<i>__namesakes` (a name step: by number or
by name, and how many rows there carry the same key). Values go
as parameters, in the order their places stand in the text; every name in
the text comes from the catalogue or a validated template. Pure: the text
and its parameters.

A name step is one hash join, never a join on an `or`: each row here
offers a key per route (its number; its folded name), each row there the
same, and the two meet on (route, key) (`named`)."""
from __future__ import annotations

from products.scan import views as cat
from products.scan.template import Template

CONTESTED_WHOLE = "the group this row belongs to is contested as a whole: the watch flagged it"
#: a link read from either end: `row_a = ref or row_b = ref` made the planner walk every link for every row (a 133,000 by
#: 2.8 million nested loop); a union of the two directions lets it use the key indexes on each
LINKS_BOTH_WAYS = ("select row_a as this, row_b as other, grade, reason, rule, decision, link_id from pub.links "
                   "union all select row_b, row_a, grade, reason, rule, decision, link_id from pub.links")
#: a name as the lanes' and the links' folds compare it (`check.loose`): lower case, macrons off, a legal ending off,
#: letters and digits only
LEGAL_ENDING = r"\m(limited|ltd|incorporated|inc|tapui)\M"


def fold_sql(x: str) -> str:
    return (f"regexp_replace(regexp_replace(translate(lower({x}), 'āēīōū', 'aeiou'), '{LEGAL_ENDING}', '', 'g'), "
            "'[^a-z0-9]', '', 'g')")


def ref_expr(i: int, view: str) -> str:
    v = cat.BY_NAME[view]
    return f"'{v.register}:' || s{i}.{v.key_col}"


def _where(i: int, where: tuple, params: list) -> list:
    out = []
    for col, val in where:
        if val is None:
            out.append(f"s{i}.{col} is null")
        elif isinstance(val, bool):
            out.append(f"s{i}.{col} is {'true' if val else 'false'}")
        elif isinstance(val, tuple):
            out.append(f"s{i}.{col} = any(%s)")
            params.append(list(val))
        else:
            out.append(f"s{i}.{col} = %s")
            params.append(val)
    return out


def _land(i: int, view: str, other: str) -> str:
    """How the next view's row is reached from the other side's ref: a row
    pub.names carries, by its view and key; an organisation row (not in
    pub.names), by the register prefix and the key."""
    v = cat.BY_NAME[view]
    if v.person_row:
        return (f"join pub.names n{i} on n{i}.ref = {other} and n{i}.view = '{v.name}'\n"
                f"join pub.{v.name} s{i} on s{i}.{v.key_col} = n{i}.key")
    return f"join pub.{v.name} s{i} on {other} like '{v.register}:%%' and s{i}.{v.key_col} = split_part({other}, ':', 2)"


def _offers(h: str, here: str, number: tuple) -> str:
    """What a row here offers a name step: (route, key) per route."""
    out = [f"('name', {fold_sql(f'{h}.{here}')})"]
    if number:
        out.insert(0, f"('number', nullif({h}.{number[0]}::text, ''))")
    return "values " + ", ".join(out)


def _there(view: str, there: str, number: tuple, namesakes: bool) -> str:
    """Every row of pub.<view> under each route it offers (`__by`, `__val`),
    with how many rows of the view offer the same key (`__namesakes`; 1
    unless the step counts namesakes)."""
    f = fold_sql(f"x.{there}")
    count = (lambda e: f"count(*) over (partition by {e})") if namesakes else (lambda e: "1")
    sides = [f"select 'name'::text as __by, {f} as __val, {count(f)} as __namesakes, x.* from pub.{view} x"]
    if number:
        n = f"nullif(x.{number[1]}::text, '')"
        sides.insert(0, f"select 'number'::text as __by, {n} as __val, {count(n)} as __namesakes, x.* "
                        f"from pub.{view} x where {n} is not null")
    return "(" + " union all ".join(sides) + ")"


def _guard(k: str, h: str, t: str, number: tuple) -> str:
    """Two rows that both carry a number meet by it or not at all."""
    if not number:
        return ""
    return f" and not ({k}.by = 'name' and nullif({h}.{number[0]}::text, '') is not null and nullif({t}.{number[1]}::text, '') is not null)"


def named(i: int, p: int, pview: str, view: str, on: tuple, number: tuple, optional: bool, namesakes: bool = False) -> str:
    """The join of a name step. Inner: the row here offers its keys and
    meets the rows there on (route, key), in the line's own query, so only
    the rows the line reaches are folded. Optional: the same meeting made
    for every row of pub.<pview> in a subquery keyed by the row (`__hk`),
    then left-joined, so a row with nothing there gives one line, not one
    per route."""
    here, there = on
    if not optional:
        return (f"cross join lateral ({_offers(f's{p}', here, number)}) k{i}(by, val)\n"
                f"join {_there(view, there, number, namesakes)} s{i} on s{i}.__by = k{i}.by and s{i}.__val = k{i}.val and k{i}.val <> ''"
                + _guard(f"k{i}", f"s{p}", f"s{i}", number))
    pk = cat.BY_NAME[pview].key_col
    return (f"left join (select h.{pk} as __hk, t.*\n  from pub.{pview} h\n  cross join lateral ({_offers('h', here, number)}) k(by, val)\n"
            f"  join {_there(view, there, number, namesakes)} t on t.__by = k.by and t.__val = k.val\n"
            f"  where k.val <> ''{_guard('k', 'h', 't', number)}) s{i} on s{i}.__hk = s{p}.{pk}")


OPTIONAL = frozenset({"document", "page", "place"})   # a citation's columns: read where the view has them (a copied register's rows may lack a document)


def sql(t: Template, settings: dict, start: str, limit: int | None = None, have: dict = None) -> tuple:
    """(text, params) for the scan started from `start` (one of the first
    step's views). `settings` is settings.in_force(); `have` is {view: its
    columns} read from the database, so an optional column a view lacks is
    left out (None: every column is selected)."""
    if start not in t.steps[0].views:
        raise ValueError(f"{t.name} does not start from pub.{start}")
    chains = settings["chains"]["value"]
    select, joins, where, order = [], [], [], []
    join_params, where_params = [], []
    for i, s in enumerate(t.steps):
        view = start if i == 0 else s.view
        v = cat.BY_NAME[view]
        for c in sorted(cat.columns_read(v) | set(s.columns)):
            if c in OPTIONAL and have is not None and c not in have.get(view, set()):
                continue
            select.append(f"s{i}.{c} as s{i}__{c}")
        order.append(f"s{i}.{v.key_col}")
        if i == 0:
            joins.append(f"from pub.{view} s0")
            where += _where(0, s.where, where_params)
            continue
        p = i - 1
        pview = start if p == 0 else t.steps[p].view
        pref = ref_expr(p, pview)
        kind = "left join" if s.optional else "join"
        if s.by == "row":
            here, there = s.on
            joins.append(f"{kind} pub.{view} s{i} on s{i}.{there} = s{p}.{here}")
        elif s.by == "name":
            joins.append(named(i, p, pview, view, s.on, s.number, s.optional, s.namesakes))
            select += [f"s{i}.__by as s{i}__by", f"s{i}.__namesakes as s{i}__namesakes"]
        elif s.by == "person" and chains == "follow":
            joins.append(f"join pub.groups ga{i} on ga{i}.row_key = {pref}\n"
                         f"join pub.groups gb{i} on gb{i}.group_id = ga{i}.group_id and gb{i}.row_key <> ga{i}.row_key\n"
                         + _land(i, view, f"gb{i}.row_key"))
            select.append(f"(ga{i}.contested or gb{i}.contested) as s{i}__contested")
            select.append(f"ga{i}.group_id as s{i}__group")
        else:   # a direct confirmed link, or a link of a named rule (or rules)
            cond = f"l{i}.this = {pref}"
            if s.by == "person":
                cond += f" and l{i}.grade = 'confirmed'"
            elif len(s.rules) > 1:
                cond += f" and l{i}.rule = any(%s)"
                join_params.append(list(s.rules))
            else:
                cond += f" and l{i}.rule = %s"
                join_params.append(s.rules[0] if s.rules else s.rule)
            joins.append(f"join ({LINKS_BOTH_WAYS}) l{i} on {cond}\n" + _land(i, view, f"l{i}.other"))
            select += [f"l{i}.grade as s{i}__grade", f"l{i}.reason as s{i}__reason", f"l{i}.rule as s{i}__rule",
                       f"l{i}.decision as s{i}__decision", f"l{i}.link_id as s{i}__link"]
        if s.optional:   # a filter on an optional step joins nothing rather than dropping the line
            joins[-1] += "".join(f" and {w}" for w in _where(i, s.where, join_params))
        else:
            where += _where(i, s.where, where_params)
    params = join_params + where_params
    text = "select\n  " + ",\n  ".join(select) + "\n" + "\n".join(joins)
    if where:
        text += "\nwhere " + "\n  and ".join(where)
    text += "\norder by " + ", ".join(order)
    if limit:
        text += "\nlimit %s"
        params.append(int(limit))
    return text, params


def views_read(t: Template) -> list:
    """Every pub view the query touches, in order: the register views, then the links' (when a step uses them)."""
    out = []
    for v in list(t.steps[0].views) + [s.view for s in t.steps[1:]]:
        if v not in out:
            out.append(v)
    if t.uses_links:
        out += [x for x in cat.LINKS_VIEWS if x not in out]
    return out
