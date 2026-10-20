"""The report's outside check (spec line 4), against the real published
tables through the product reader, never the sample:

  1. A report on a known donor names its returns, the company behind it
     and that company's directors, each with its citation. The donor is
     taken from the tables at run time (a donor row name-linked to a company
     that has directors in the latest file), so the check fails if the
     shape breaks, not if the data moves.
  2. Nothing the registers do not hold: every citation names a row that is
     in its published view today.
  3. The presentation rules hold on that report and on a report from a
     company row and from a director row (dated or undated; cited; no word
     of cause; no owner; blanks say none found or not held; no suppressed
     name; near with a reason).
  4. Every column the catalogue reads exists in its view; no address-shaped
     column is read outside the registered-office view (hard limit 15).
  5. Every template on disk loads, and names only published views.
  6. The memo prints, as text and as HTML, with every citation numbered.
  7. A register's own words are not read as the report's: a report on a
     donor whose name carries a street word and on a company whose name
     carries a word of cause (both taken from the tables at run time) is
     not refused; the rules still refuse a planted fault (the fast tests).

  python -m products.report check [--ref REF]      exit 1 on any failure
"""
from __future__ import annotations

import re
import sys

from products.report import build, catalogue as cat, db, memo, rules, template as tpl

ADDRESS_WORDS = re.compile(r"residential|home_address|street|suburb|postal", re.I)


def known_donor(conn) -> tuple:
    got = db.rows(conn, """
        select l.row_b as donor_ref, split_part(l.row_a, ':', 2) as company_key
        from pub.links l
        where l.rule = 'organisation-name@1' and l.row_a like 'companies:%%' and l.row_b like 'party_returns:%%'
          and exists (select 1 from pub.directors d where d.entity_key = split_part(l.row_a, ':', 2) and d.in_latest and not coalesce(d.suppressed, false))
        order by l.row_b limit 1""")
    return (got[0]["donor_ref"], got[0]["company_key"]) if got else (None, None)


def cited_rows_exist(conn, report: dict) -> list:
    out = []
    for c in report["citations"]:
        v = cat.BY_NAME.get(c["view"])
        if not v:
            out.append(f"citation [{c['n']}] names pub.{c['view']}, which the catalogue does not know")
            continue
        hit = conn.execute(f"select 1 from pub.{v.name} where {v.key_col} = %s limit 1", (c["key"],)).fetchone()
        if not hit:
            out.append(f"citation [{c['n']}] pub.{c['view']} {c['key']}: no such row in the published view")
    return out


STREET_NAMED = r"\m(lane|place|street|drive|terrace|road|crescent)\M"
CAUSE_NAMED = r"\m(control|controls|behind|beneficial|owner|owners)\M"


def own_words_not_refused(conn, subject, held: set) -> list:
    """A donor surnamed with a street word and a company named with a word of
    cause, from the tables today: their reports are not refused for rules 3,
    4 or 7, because those are the register's words. Each is named so the
    failure says which row."""
    out = []
    picks = []
    for sql, label in ((f"select key from pub.party_return_donors where donor ~* %s and donor !~ '\\d' order by key limit 1", "party_returns"),
                       (f"select c.key from pub.companies c where c.name ~* %s and exists (select 1 from pub.directors d where d.entity_key = c.key and d.in_latest) order by c.key limit 1", "companies")):
        got = db.rows(conn, sql, (STREET_NAMED if label == "party_returns" else CAUSE_NAMED,))
        if not got:
            out.append(f"no row to check rules 3, 4 and 7 against a register's own words in {label}")
            continue
        picks.append(f"{label}:{got[0]['key']}")
    for ref in picks:
        r = build.build(conn, ref, subject, held)
        if not r["found"]:
            out.append(f"{ref}: not found")
            continue
        out += [f"{ref}: {p}" for p in r["problems"] if "(rule 3)" in p or "(rule 4)" in p or "(rule 7)" in p]
    return out


def problems(conn, ref: str = None) -> list:
    out = []
    held = db.pub_views(conn)
    # 4. columns
    for v in cat.VIEWS:
        if v.name not in held:
            out.append(f"{v.name}: in the catalogue but not published")
            continue
        cols = {r["column_name"] for r in db.rows(conn, "select column_name from information_schema.columns where table_schema = 'pub' and table_name = %s", (v.name,))}
        for c in sorted(cat.columns_read(v) - cols):
            out.append(f"{v.name}: the report reads `{c}`, which pub.{v.name} does not carry")
        for c in cols & cat.columns_read(v):
            if ADDRESS_WORDS.search(c) and v.name != "company_addresses":
                out.append(f"{v.name}: reads `{c}`, an address-shaped column outside the registered-office view")
    # 5. templates
    for name, folder in tpl.folders().items():
        try:
            t = tpl.load(folder)
        except Exception as exc:
            out.append(f"template {name}: does not load: {exc}")
            continue
        for v in sorted(t.views - held):
            out.append(f"template {name}: reads pub.{v}, which is not published")
    if out:
        return out
    subject = tpl.by_name("subject")
    # 1. the done-when
    if ref is None:
        ref, company_key = known_donor(conn)
        if not ref:
            return out + ["no donor row is name-linked to a company with directors: the done-when cannot be checked"]
    else:
        company_key = None
    r = build.build(conn, ref, subject, held)
    if not r["found"]:
        return out + [f"{ref}: {r['why']}"]
    out += [f"{ref}: {p}" for p in r["problems"]]
    money = [s for s in r["sections"] if s["name"] == "money"]
    if company_key:
        if not money or not any(it["view"] == "party_return_totals" and it.get("cite") for it in money[0]["items"]):
            out.append(f"{ref}: the report does not name the subject's return")
        comp = [s for s in r["sections"] if s["name"] == "companies"]
        items = comp[0]["items"] if comp else []
        company = [it for it in items if it["ref"] == f"companies:{company_key}"]
        if not company or not company[0].get("cite"):
            out.append(f"{ref}: the company behind the donor ({company_key}) is not named with a citation")
        elif company[0]["grade"] != "near" or not company[0]["reason"]:
            out.append(f"{ref}: the company is reached by a name match and must be near, with its reason")
        directors = [it for it in items if it["view"] == "directors" and it["via"] == f"companies:{company_key}" and it.get("cite")]
        if not directors:
            out.append(f"{ref}: the company's directors are not named with citations")
    # 2. nothing the registers do not hold
    out += cited_rows_exist(conn, r)
    # 7. a register's own words are not the report's
    out += own_words_not_refused(conn, subject, held)
    # 6. the memo prints
    text = memo.text(r)
    html = memo.html_body(r)
    for c in r["citations"]:
        if f"[{c['n']}]" not in text:
            out.append(f"citation [{c['n']}] is numbered but never printed in the text memo")
            break
    if "CITATIONS" not in text or "<h3>Citations</h3>" not in html:
        out.append("the memo has no citations list")
    if "none found" not in text and "not held" not in text:
        out.append("the memo never says none found or not held: every report has a register it did not reach")
    # 3. the rules on a company row and a director row too
    if company_key:
        for other in (f"companies:{company_key}",) + tuple(f"companies:{d['key']}" for d in db.rows(
                conn, "select key from pub.directors where entity_key = %s and in_latest order by key limit 1", (company_key,))):
            r2 = build.build(conn, other, subject, held)
            if not r2["found"]:
                out.append(f"{other}: not found")
                continue
            out += [f"{other}: {p}" for p in r2["problems"]]
            out += cited_rows_exist(conn, r2)
    return out


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else None
    with db.scan_connect() as conn:
        bad = problems(conn, ref)
    for b in bad:
        print("PROBLEM " + b)
    print("products.report check: " + ("green" if not bad else f"{len(bad)} problem(s)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
