"""The start page's name search (ruling 92 item 7): a reader types a person,
company or organisation name and gets the rows that carry it, each a link
that runs the report on that row; nobody is asked for a row reference.

It is the board's search (products/board/search.py) and nothing new: every
word must begin a word of the row's search columns, macrons folded; a term
that is all digits also matches an official number exactly; a suppressed or
revoked row never matches by name (hard limit 16); up to ten rows per view,
with the view's count. Products may import only support/ (imports run one
way), so the pieces under "from products/board/search.py" are the board's
source character for character, and the columns under SEARCH are the
board's catalogue's; tests/test_search.py holds both equal by reading the
board's files, never by importing them. Change the board, then copy here.

The report searches the views it can start from (its catalogue) that name a
person or an organisation, apart from a view whose text may be withheld.
One connection, one view after another, under the page's lock: the product
reader's connections are shared (lessons: a shared read role's cap)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from products.report import catalogue as cat
from products.report import db

LIMIT = 10          # rows per view, as the board's "same name elsewhere"
MAX_TERM = 100


@dataclass(frozen=True)
class Searched:
    """A report view as the board's search reads it."""
    name: str
    register: str
    search: tuple
    numbers: tuple = ()
    suppressed: str = ""
    hide_names: tuple = ()
    default_order: str = "key"
    key_col: str = "key"


#: {view: (search, numbers, default_order)}, the board catalogue's own values for the view
SEARCH = {
    "companies": (("name",), ("nzbn", "number"), "key"),
    "directors": (("full_name", "last_name"), (), "key"),
    "shareholders": (("name",), ("holder_nzbn",), "key"),
    "company_states": (("name",), (), "key"),
    "societies": (("name",), ("nzbn", "number"), "key"),
    "society_officers": (("full_name", "last_name"), (), "key"),
    "charities": (("name", "other_names"), ("number", "nzbn", "incorporation_number"), "key"),
    "charity_officers": (("full_name", "last_name"), (), "key"),
    "party_return_totals": (("party", "party_label"), (), "year"),
    "party_return_donors": (("donor",), (), "ordinal"),
    "party_return_loans": (("lender",), (), "ordinal"),
    "disclosures": (("donor_name", "party", "party_label"), (), "received_on"),
    "disclosure_items": (("contributor", "text"), (), "key"),
    "candidate_return_totals": (("surname", "given_names", "electorate", "party"), (), "year"),
    "candidate_return_donors": (("donor", "surname", "electorate"), (), "ordinal"),
    "gazette_liquidations": (("company",), ("company_number",), "published_on"),
    "gazette_company_notices": (("company", "party"), ("company_number",), "published_on"),
    "gazette_possessions": (("mortgagee", "mortgagor"), ("mortgagee_number", "mortgagor_number"), "published_on"),
    "gazette_liquidators": (("name",), (), "published_on"),
    "gazette_practitioners": (("name",), (), "published_on"),
    "gazette_prohibitions": (("name", "also_known_as"), (), "published_on"),
    "gazette_bankruptcies": (("surname", "given_names", "also_known_as"), (), "published_on"),
    "gazette_appointments": (("name", "body", "role"), (), "published_on"),
    "candidates": (("name", "display_name", "party", "party_registered", "electorate"), (), "election"),
    "members": (("name", "display_name", "party", "party_registered", "electorate"), (), "from_on"),
    "mp_interest_returns": (("name", "member", "party", "party_label", "electorate"), (), "as_at"),
    "mp_expenses": (("name", "member", "party", "party_label"), (), "period_start"),
    "minister_expenses": (("name", "member", "party", "party_label"), (), "period_start"),
    "parties": (("name", "first_name", "abbreviation", "secretary"), (), "key"),
    "promoters": (("promoter",), (), "year"),
    "promoter_people": (("name", "promoter"), (), "key"),
}


def searched_views() -> list:
    """The catalogue's views that name a person or an organisation and carry
    no withheld text, in the catalogue's order, as the search reads them."""
    out = []
    for v in cat.VIEWS:
        if v.name not in SEARCH or not v.names or v.withheld:
            continue
        s, n, order = SEARCH[v.name]
        out.append(Searched(v.name, v.register, s, n, v.suppressed, v.hide_names, order, v.key_col))
    return out


# ── from products/board/search.py ──

MACRON_FROM, MACRON_TO = cat.MACRONS


def fold_sql(expr: str) -> str:
    return f"translate(lower({expr}), '{MACRON_FROM}', '{MACRON_TO}')"


def words_of(term: str) -> list:
    return [w for w in re.split(r"[\s,;]+", cat.fold_term(term)) if w]


def is_number(term: str) -> bool:
    return bool(re.fullmatch(r"\d[\d ]*", term.strip()))


def guard_sql(v: cat.View, exclude_key: str = None) -> tuple:
    """A suppressed or revoked row is never matched by name (hard limit 16)."""
    clause, params = "", []
    if v.suppressed:
        clause += f" and not coalesce({v.suppressed}, false)"
    if v.hide_names:
        clause += f" and not coalesce({v.hide_names[0]}, '') ~* %s"
        params.append(v.hide_names[1])
    if exclude_key:
        clause += f" and {v.key_col} <> %s"
        params.append(exclude_key)
    return clause, params


# ── the board's match_sql and view_sql, without the expanded search's fields (ruling 82), which the report does not offer ──

def match_sql(v: Searched, words: list, number: str = None) -> tuple:
    """(clause, params): each word begins a word of the row's search columns, or the number is an official number."""
    haystack = fold_sql("concat_ws(' ', " + ", ".join(v.search) + ")")
    where, params = [], []
    for w in words:
        where.append(f"{haystack} ~ %s")
        params.append(r"\m" + re.escape(w))
    clause = "(" + " and ".join(where) + ")" if where else ""
    if number and v.numbers:
        clause = "(" + (clause or "false") + " or " + " or ".join(f"{c} = %s" for c in v.numbers) + ")"
        params += [number] * len(v.numbers)
    return (clause or "false"), params


def view_sql(v: Searched, words: list, number: str = None, limit: int = LIMIT) -> tuple:
    """(sql, params): the matching rows of one view with the view's total as `total` on every row."""
    clause, params = match_sql(v, words, number)
    g, gp = guard_sql(v)
    sql = (f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} where {clause}{g} "
           f"order by {v.default_order} nulls last, {v.key_col} limit %s")
    return sql, params + gp + [limit]


def search(conn, term: str, limit: int = LIMIT) -> list:
    """[(catalogue view, total, rows)] for the searched views that matched, in
    the catalogue's order; a view not published is passed over."""
    term = (term or "").strip()[:MAX_TERM]
    words = words_of(term)
    number = re.sub(r"\s", "", term) if is_number(term) else None
    if not words and not number:
        return []
    held = db.pub_views(conn)
    out = []
    for s in searched_views():
        if s.name not in held:
            continue
        sql, params = view_sql(s, words, number, limit)
        found = db.rows(conn, sql, params)
        if found:
            out.append((cat.BY_NAME[s.name], int(found[0]["total"]), found))
    return out
