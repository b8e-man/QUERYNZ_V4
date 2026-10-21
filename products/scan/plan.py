"""A scan's steps compiled to one query over `pub`, under the chains
setting. Each step is an alias `s<i>`; the select list carries, for every
step, the columns the catalogue reads and the template's own, named
`s<i>__<column>`, and for a person or link step the grade columns the line
builder reads: `s<i>__contested` and `s<i>__group` (a group step),
`s<i>__grade`, `s<i>__reason`, `s<i>__rule`, `s<i>__decision`, `s<i>__link`
(a link step). Values go as parameters; every name in the text comes from
the catalogue or a validated template. Pure: the text and its parameters."""
from __future__ import annotations

from products.scan import views as cat
from products.scan.template import Template

CONTESTED_WHOLE = "the group this row belongs to is contested as a whole: the watch flagged it"
#: a link read from either end: `row_a = ref or row_b = ref` made the planner walk every link for every row (a 133,000 by
#: 2.8 million nested loop); a union of the two directions lets it use the key indexes on each
LINKS_BOTH_WAYS = ("select row_a as this, row_b as other, grade, reason, rule, decision, link_id from pub.links "
                   "union all select row_b, row_a, grade, reason, rule, decision, link_id from pub.links")


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


OPTIONAL = frozenset({"document", "page", "place"})   # a citation's columns: read where the view has them (a copied register's rows may lack a document)


def sql(t: Template, settings: dict, start: str, limit: int | None = None, have: dict = None) -> tuple:
    """(text, params) for the scan started from `start` (one of the first
    step's views). `settings` is settings.in_force(); `have` is {view: its
    columns} read from the database, so an optional column a view lacks is
    left out (None: every column is selected)."""
    if start not in t.steps[0].views:
        raise ValueError(f"{t.name} does not start from pub.{start}")
    chains = settings["chains"]["value"]
    select, joins, where, params, order = [], [], [], [], []
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
            where += _where(0, s.where, params)
            continue
        p = i - 1
        pview = start if p == 0 else t.steps[p].view
        pref = ref_expr(p, pview)
        if s.by == "row":
            here, there = s.on
            joins.append(f"join pub.{view} s{i} on s{i}.{there} = s{p}.{here}")
        elif s.by == "person" and chains == "follow":
            joins.append(f"join pub.groups ga{i} on ga{i}.row_key = {pref}\n"
                         f"join pub.groups gb{i} on gb{i}.group_id = ga{i}.group_id and gb{i}.row_key <> ga{i}.row_key\n"
                         + _land(i, view, f"gb{i}.row_key"))
            select.append(f"(ga{i}.contested or gb{i}.contested) as s{i}__contested")
            select.append(f"ga{i}.group_id as s{i}__group")
        else:   # a direct confirmed link, or a link of a named rule
            cond = f"l{i}.this = {pref}"
            if s.by == "person":
                cond += f" and l{i}.grade = 'confirmed'"
            else:
                cond += f" and l{i}.rule = %s"
                params.append(s.rule)
            joins.append(f"join ({LINKS_BOTH_WAYS}) l{i} on {cond}\n" + _land(i, view, f"l{i}.other"))
            select += [f"l{i}.grade as s{i}__grade", f"l{i}.reason as s{i}__reason", f"l{i}.rule as s{i}__rule",
                       f"l{i}.decision as s{i}__decision", f"l{i}.link_id as s{i}__link"]
        where += _where(i, s.where, params)
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
