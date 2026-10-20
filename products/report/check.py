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
  8. Every template on disk gets the contract's common rules: the done-when
     donor's report under each carries group-standing, hubs-met and
     replaced-return (unless the template opts out), each keeping the contract.
  9. The walk's routes, each on a row taken from the tables at run time: an
     interests return lists its own declarations, confirmed; a sitting
     member's seat reaches expense rows by name, near with the reason; a
     donation row a confirmed link joins to a person row takes that row's
     group and says so; a winding-up notice is dated "to be heard" with its
     filing and publication days; the header lists no group row a section
     lists.

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


def routes(conn, subject, held: set) -> list:
    """The walk's routes on run-time rows (9)."""
    out = []
    # an interests return lists its declarations
    got = db.rows(conn, "select r.key from pub.mp_interest_returns r where r.declarations > 0 and exists (select 1 from pub.mp_interests i where i.member_return = r.key) "
                        "order by r.as_at desc, r.key limit 1")
    if got:
        ref = f"mp_interests:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        decl = [it for s_ in r["sections"] for it in s_["items"] if it["view"] == "mp_interests" and it.get("via") == ref]
        if not decl or any(it["grade"] != "confirmed" for it in decl):
            out.append(f"{ref}: an interests return's own declarations are not listed as confirmed ({len(decl)} listed)")
    else:
        out.append("no interests return with declarations: route 9a cannot be checked")
    # a member's seat reaches expense rows by name, near
    got = db.rows(conn, "select m.key from pub.members m where exists (select 1 from pub.mp_expenses e where e.role = 'total' "
                        "and translate(lower(e.name), 'āēīōū', 'aeiou') = translate(lower(m.display_name), 'āēīōū', 'aeiou')) order by m.from_on desc, m.key limit 1")
    if got:
        ref = f"house:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        exp = [it for s_ in r["sections"] for it in s_["items"] if it["view"] in ("mp_expenses", "minister_expenses")]
        if not exp:
            out.append(f"{ref}: a member's seat reaches no expense row by name")
        elif any(it["grade"] != "near" or not it.get("reason") for it in exp):
            out.append(f"{ref}: an expense row reached by name is not near with its reason")
        elif any(it["row"].get("role") == "category" for it in exp):
            out.append(f"{ref}: a per-category expense line is listed; only totals and money outside the total are")
    else:
        out.append("no member whose name an expense release prints: route 9b cannot be checked")
    # a donation row takes the group of the person row a confirmed link names
    got = db.rows(conn, "select l.row_b as donor from pub.links l join pub.groups g on g.row_key = l.row_a where l.grade = 'confirmed' and l.row_a like 'companies:%%/director/%%' "
                        "and l.row_b like 'party_returns:%%' and exists (select 1 from pub.groups g2 where g2.group_id = g.group_id and g2.row_key <> l.row_a) order by l.row_b limit 1")
    if got:
        ref = got[0]["donor"]
        r = build.build(conn, ref, subject, held)
        g = r["group"]
        if not g.get("via") or g.get("size", 1) < 2:
            out.append(f"{ref}: a donation row a confirmed link joins to a person row takes no group (via {g.get('via')!r}, size {g.get('size')})")
        gs = [f for f in r["flags"] if f["rule"] == "group-standing"]
        if not gs or "filed row" not in gs[0]["text"]:
            out.append(f"{ref}: the group-standing flag does not say the group is an adopted one")
    else:
        out.append("no donation row confirmed to a grouped director row: route 9c cannot be checked")
    # a winding-up notice says what its date is
    got = db.rows(conn, "select n.register_key from pub.gazette_company_notices n where n.kind = 'winding-up application' and n.event_basis = 'hearing' "
                        "and n.filed_on is not null and n.published_on is not null and n.register_key is not null and exists (select 1 from pub.companies c where c.key = n.register_key) "
                        "order by n.published_on desc, n.key limit 1")
    if got:
        ref = f"companies:{got[0]['register_key']}"
        r = build.build(conn, ref, subject, held)
        notices = [it for s_ in r["sections"] for it in s_["items"] if it["view"] == "gazette_company_notices" and it["row"].get("kind") == "winding-up application"]
        if not notices:
            out.append(f"{ref}: the winding-up notice on the company is not listed")
        elif not all("to be heard" in it["dates"]["text"] and "filed" in it["dates"]["text"] and "published" in it["dates"]["text"] for it in notices):
            out.append(f"{ref}: a winding-up notice's date does not say it is the hearing day with its filing and publication days: {notices[0]['dates']['text']!r}")
    else:
        out.append("no winding-up notice joined to a company: route 9d cannot be checked")
    # the header repeats nothing a section lists
    got = db.rows(conn, "select g.row_key from pub.groups g join pub.names n on n.ref = g.row_key where n.view = 'directors' "
                        "and (select count(*) from pub.groups g2 where g2.group_id = g.group_id) between 2 and 6 order by g.row_key limit 1")
    if got:
        ref = got[0]["row_key"]
        r = build.build(conn, ref, subject, held)
        listed = {it["ref"] for s_ in r["sections"] for it in s_["items"]}
        twice = [m["ref"] for m in r["members"] if m["ref"] in listed]
        if twice:
            out.append(f"{ref}: the header repeats {len(twice)} group row(s) a section lists")
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
    # 9. the walk's routes
    out += routes(conn, subject, held)
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
    # 8. every template on disk carries the common rules
    for name, folder in tpl.folders().items():
        t = tpl.load(folder)
        if name == "subject" or not t.common_rules:
            continue
        rt = build.build(conn, ref, t, held)
        have = {f["rule"] for f in rt["flags"]}
        for want in ("group-standing", "hubs-met", "replaced-return"):
            if want not in have:
                out.append(f"template {name}: the report on {ref} carries no {want} flag; the contract's common rules did not run")
        out += [f"template {name} on {ref}: {p}" for p in rt["problems"] if "rule 9" in p]
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
