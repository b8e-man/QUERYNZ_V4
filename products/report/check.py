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
 10. The third tranche's routes (routes_3), each on a run-time row: a
     company named like a street address is shown, not refused; a
     possession notice on the borrower, dated "entered", and new since the
     day it was entered; a company's earlier state dated by its file and
     kept by a changed section; a company holder followed up the chain by
     name, near, shares as filed; a director's other current company
     reached from a company start, near, through the director's row, and
     held apart by a section's `own`; the companies at a shared office; a
     filed row's standing; the start's own company confirmed in a contested
     group; practitioners via the notice; a holding hub; a Crown body.
 10. The fix-report-2 routes (`routes_4`): a company's charity by business
     number with its officers; a director's namesake charity officer near
     by name; a charity's returns newest first, dated 'period to'; a
     template naming charities as not held loads and says it is published.

 11. The start page's name search (ruling 92 item 7), over HTTP on the
     page's own server on a passing port: the done-when company's name
     answers 200 with no row-reference wording, lists the rows as report
     links, and its first link answers 200 with a memo that says in plain
     words where it starts; every searched view carries its search columns.

  python -m products.report check [--ref REF]      exit 1 on any failure
"""
from __future__ import annotations

import datetime as dt
import html as htmllib
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

from products.report import build, catalogue as cat, db, memo, rules, search, template as tpl, walk

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
            out.append(f"{ref}: a member's seat reaches no expense row by name or by link")
        elif any(it["grade"] == "near" and not it.get("reason") for it in exp):
            out.append(f"{ref}: an expense row reached by name is not near with its reason")
        elif any(it["grade"] == "confirmed" and not (it.get("rule") or it.get("via") == ref) for it in exp):
            out.append(f"{ref}: an expense row listed as confirmed names no link rule and is not of the seat's own group")
        elif any(it["row"].get("role") not in walk.EXPENSE_ROLES for it in exp):
            out.append(f"{ref}: a per-category expense line is listed; only totals and money outside the total are, by name or by link")
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


def _items(r: dict, view: str = None) -> list:
    return [it for s_ in r["sections"] for it in s_["items"] if view is None or it["view"] == view]


def routes_3(conn, subject, held: set) -> list:
    """The third tranche's routes, each on a row taken from the tables at run
    time (the cards of 21 October)."""
    out = []
    # a company named like a street address is shown as the register names it (hard limit 15 shows a company's address; rule 7 keeps a person's)
    got = db.rows(conn, "select key from pub.companies where name ~ '^[0-9]+[A-Z]? ' and name ~* '(street|road|terrace|lane|avenue|drive|place|crescent) limited$' "
                        "and exists (select 1 from pub.directors d where d.entity_key = companies.key and d.in_latest) order by key limit 1")
    if got:
        ref = f"companies:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        out += [f"{ref}: a company named like an address refuses its own report: {p}" for p in r["problems"] if "(rule 7)" in p]
        d = db.rows(conn, "select key from pub.directors where entity_key = %s and in_latest order by key limit 1", (got[0]["key"],))
        if d:
            r2 = build.build(conn, f"companies:{d[0]['key']}", subject, held)
            out += [f"companies:{d[0]['key']}: a director's walk meeting a company named like an address is refused: {p}" for p in r2["problems"] if "(rule 7)" in p]
    else:
        out.append("no company named like a street address with a director: the rule 7 exemption cannot be checked")
    # a mortgagee's entry into possession is listed on the borrower company, dated 'entered'
    got = db.rows(conn, "select mortgagor_register_key as k from pub.gazette_possessions where mortgagor_register_key is not null and entered_on is not null "
                        "and exists (select 1 from pub.companies c where c.key = gazette_possessions.mortgagor_register_key) order by published_on desc, key limit 1")
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        poss = _items(r, "gazette_possessions")
        if not poss:
            out.append(f"{ref}: the possession notice on the company is not listed")
        elif not all("entered" in it["dates"]["text"] and it["grade"] == "confirmed" for it in poss):
            out.append(f"{ref}: a possession notice is not dated 'entered' and confirmed: {poss[0]['dates']['text']!r}")
        # the since date: the notice is new since the day it was entered, and not new since the day after
        entered = poss[0]["dates"]["on"] if poss else None
        if entered:
            latest = max(x for x in (entered, poss[0]["dates"].get("published")) if x)   # a row is new when any of its dates is on or after the since date
            r_new = build.build(conn, ref, subject, held, since=entered)
            r_old = build.build(conn, ref, subject, held, since=latest + dt.timedelta(days=1))
            if not [it for it in _items(r_new, "gazette_possessions") if it.get("new")] or r_new.get("new", 0) < 1:
                out.append(f"{ref}: since {entered}: the possession entered that day is not marked new")
            if [it for it in _items(r_old, "gazette_possessions") if it.get("new") and it["dates"]["on"] == entered]:
                out.append(f"{ref}: since {latest + dt.timedelta(days=1)}: a possession entered and published before it is marked new")
            if "since " not in memo.text(r_new):
                out.append(f"{ref}: the memo does not print the since date")
    else:
        out.append("no possession notice on a company: the possessions route cannot be checked")
    # a company's earlier state is listed, dated by its file; a changed section keeps it with the file that shows the change
    got = db.rows(conn, "select entity_key as k from pub.company_states where exists (select 1 from pub.companies c where c.key = company_states.entity_key) order by key limit 1")
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        st = _items(r, "company_states")
        if not st or not all("as in the file" in it["dates"]["text"] and not it["dates"]["undated"] for it in st):
            out.append(f"{ref}: the company's earlier state is not listed dated by its file ({len(st)} listed)")
        t = tpl.Template("check-changed", "check", "0", "check", "", subject.reads,
                         (tpl.Section("changed", "Changed", ("companies", "directors", "shareholders", "company_addresses", "company_states"), changed=True),
                          tpl.Section("rest", "Rest", ("companies", "directors", "shareholders", "company_addresses", "company_states"))), depth=1)
        rc = build.build(conn, ref, t, held)
        ch = rc["sections"][0]["items"]
        if not any(it["view"] == "company_states" and it.get("changed_in") for it in ch):
            out.append(f"{ref}: a changed section does not keep the earlier state with the file that shows the change")
        if any(not it.get("changed_in") for it in ch):
            out.append(f"{ref}: a changed section keeps a row that is no change")
    else:
        out.append("no company with an earlier state: the states route cannot be checked")
    # the chain: a company holder of record whose name one company carries is followed to its own row, near by name, with the shares carried
    got = db.rows(conn, "select s.entity_key as k from pub.shareholders s where s.in_latest and s.shareholder_type = 'company' "
                        "and (select count(*) from pub.companies c where c.name = s.name) = 1 order by s.key limit 1")
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        up = [it for it in _items(r, "companies") if it.get("depth") and it.get("hop_text")]
        if not up:
            out.append(f"{ref}: a company holder of record is not followed to its own register row")
        elif not all(it["grade"] == "near" and "name only" in (it.get("reason") or "") and "shares of record" in it["hop_text"] and it["dates"]["text"] for it in up if it["depth"] == 1):
            out.append(f"{ref}: a chain hop by name is not near with its reason, the shares as filed and a date or undated")
        if r["walk"]["chain"].get("depth", 0) < 1 or r["walk"]["chain_depth"] != subject.chain_depth:
            out.append(f"{ref}: the chain's depth is not stated ({r['walk']['chain']})")
        if "holding chain was followed" not in memo.text(r):
            out.append(f"{ref}: the memo does not say how far the chain was followed")
    else:
        out.append("no company holder whose name one company carries: the chain route cannot be checked")
    # from a company start its officers are followed one step: another current company of a director, near, through the director's row
    got = db.rows(conn, "select d.entity_key as k from pub.directors d join pub.groups g on g.row_key = 'companies:' || d.key "
                        "join pub.groups g2 on g2.group_id = g.group_id and g2.row_key <> g.row_key join pub.names n on n.ref = g2.row_key and n.view = 'directors' "
                        "where d.in_latest and not coalesce(d.suppressed, false) and not g.contested order by d.key limit 1")
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        through = [it for it in _items(r) if it.get("through") and it.get("rule") == "through-officer"]
        if not any(it["view"] == "companies" for it in through):
            out.append(f"{ref}: a director's other current company is not reached from the company start ({r['walk']['officers_followed']} officers followed)")
        elif not all(it["grade"] == "near" and "through a person on the subject" in (it.get("reason") or "") and it["through"].startswith(ref + "/") for it in through):
            out.append(f"{ref}: an officer's other row is not near, with the through-officer reason, via the officer's row on the start")
        elif any(it["view"] == "directors" and not walk.current_role(it["row"]) for it in through):
            out.append(f"{ref}: an officer's ended or left role is listed as a current one")
        tw = tpl.Template("check-own", "check", "0", "check", "", subject.reads,
                          (tpl.Section("own", "Own", ("companies", "directors", "shareholders", "company_addresses"), own=True),
                           tpl.Section("theirs", "Theirs", ("companies", "directors", "shareholders", "company_addresses"), own=False)), depth=1)
        ro = build.build(conn, ref, tw, held)
        own, theirs = ro["sections"]
        if not any(it["view"] == "directors" and it["via"] == ref for it in own["items"]) or any(it.get("through") for it in own["items"]):
            out.append(f"{ref}: a section asking for the start's own rows does not hold its directors apart from its people's companies")
        if not any(it.get("through") for it in theirs["items"]) or any(it["via"] == ref for it in theirs["items"]):
            out.append(f"{ref}: a section asking for the people's rows holds the start's own")
    else:
        out.append("no company with a director in an uncontested group with another directorship: the officers route cannot be checked")
    # the companies at the start's registered office are listed, near, when the office is not a hub
    cands = db.rows(conn, "select a.entity_key as k, a.line_1, a.line_2, a.postcode from pub.company_addresses a where a.in_latest and exists (select 1 from pub.company_addresses b "
                          "where b.in_latest and b.line_1 = a.line_1 and coalesce(b.line_2, '') = coalesce(a.line_2, '') and coalesce(b.postcode, '') = coalesce(a.postcode, '') "
                          "and b.entity_key <> a.entity_key) order by a.key limit 30")
    pick = None
    for c in cands:
        n = db.rows(conn, "select count(distinct entity_key) as n from pub.company_addresses where in_latest and line_1 = %s and coalesce(line_2, '') = %s and coalesce(postcode, '') = %s",
                    (c["line_1"], c["line_2"] or "", c["postcode"] or ""))[0]["n"]
        if 2 <= n < walk.SETTINGS["busy_address"]:
            pick = (c["k"], n)
            break
    if pick:
        ref = f"companies:{pick[0]}"
        r = build.build(conn, ref, subject, held)
        at = [it for it in _items(r, "companies") if it.get("rule") == "shared-office"]
        if not at:
            out.append(f"{ref}: the {pick[1] - 1} other companies at the subject's office are not listed")
        elif not all(it["grade"] == "near" and "office is not a person" in (it.get("reason") or "") for it in at):
            out.append(f"{ref}: a company at the subject's office is not near with the shared-office reason")
        elif r["walk"]["office_companies"] != pick[1]:
            out.append(f"{ref}: the walk counts {r['walk']['office_companies']} companies at the office; the view holds {pick[1]}")
    else:
        out.append("no registered office shared by two to forty-nine companies among the first thirty: the office route cannot be checked")
    # a filed row no confirmed link names a person for: group-standing says it has no group, never that it is an organisation
    got = db.rows(conn, "select d.key from pub.party_return_donors d where not exists (select 1 from pub.links l where l.grade = 'confirmed' "
                        "and (l.row_a = 'party_returns:' || d.key or l.row_b = 'party_returns:' || d.key)) order by d.key limit 1")
    if got:
        ref = f"party_returns:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        gs = [f for f in r["flags"] if f["rule"] == "group-standing"]
        if not gs or "organisation" in gs[0]["text"] or "no group" not in gs[0]["text"]:
            out.append(f"{ref}: group-standing on a filed row with no group says {gs[0]['text'] if gs else 'nothing'!r}")
    else:
        out.append("no donor row without a confirmed link: the filed-row standing route cannot be checked")
    # in a contested group the start row's own company is confirmed, whichever member reaches it first
    got = db.rows(conn, "select g.row_key from pub.groups g where g.contested and g.row_key like 'companies:%%/shareholder/%%' order by 1 limit 1")
    if got:
        ref = got[0]["row_key"]
        r = build.build(conn, ref, subject, held)
        own_key = r["subject"]["row"].get("entity_key")
        company = [it for it in _items(r, "companies") if it["ref"] == f"companies:{own_key}"]
        if not company:
            out.append(f"{ref}: the start row's own company is not listed")
        elif company[0]["grade"] != "confirmed":
            out.append(f"{ref}: the start row's own company is graded {company[0]['grade']} in a contested group: {company[0].get('reason')!r}")
    else:
        out.append("no shareholder row in a contested group: the own-entity route cannot be checked")
    # the practitioners a liquidation notice names are reached from the notice on the company
    got = db.rows(conn, "select l.register_key as k from pub.gazette_liquidations l where l.register_key is not null and exists (select 1 from pub.gazette_liquidators x where x.notice = l.notice) "
                        "and exists (select 1 from pub.companies c where c.key = l.register_key) order by l.published_on desc, l.key limit 1")
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        liq = _items(r, "gazette_liquidators")
        if not liq or not all(it["via"].startswith("gazette:") and "notice on" in it["statement"] for it in liq):
            out.append(f"{ref}: the practitioners on the company's liquidation notice are not listed via the notice ({len(liq)} listed)")
    else:
        out.append("no liquidation notice with practitioner rows on a company: the practitioners route cannot be checked")
    # a holder of record in fifty companies or more is a hub by its count, not only by its name
    got = db.rows(conn, "select name from pub.shareholders where in_latest and shareholder_type = 'company' group by name having count(distinct entity_key) >= %s order by 1 limit 1",
                  (walk.SETTINGS["hub_holdings"],))
    if got:
        k = db.rows(conn, "select entity_key as k from pub.shareholders where in_latest and name = %s order by key limit 1", (got[0]["name"],))[0]["k"]
        ref = f"companies:{k}"
        r = build.build(conn, ref, subject, held)
        hubs = [h for h in r["hubs"] if h["kind"] == "holding-hub"]
        if not hubs:
            out.append(f"{ref}: a holder of record in {walk.SETTINGS['hub_holdings']} companies or more is not flagged as a hub")
    else:
        out.append("no holder of record in fifty companies: the holding-hub route cannot be checked")
    # a Crown body holding shares is a hub by its register name
    names = sorted({x.upper() for x in walk.CROWN_BODIES} | {x.upper() + " LIMITED" for x in walk.CROWN_BODIES})
    got = db.rows(conn, "select entity_key as k from pub.shareholders where in_latest and translate(upper(name), 'ĀĒĪŌŪ', 'AEIOU') = any(%s) order by key limit 1", (names,))
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        if not [h for h in r["hubs"] if h["kind"] == "crown"]:
            out.append(f"{ref}: a Crown body holding shares is not flagged as the Crown")
    else:
        out.append("no Crown body holds shares by its register name: the Crown-body route cannot be checked")
    return out


def routes_4(conn, subject, held: set) -> list:
    """The fix-report-2 routes (the cards of 21 October), each on a row
    taken from the tables at run time: a company's charity by business
    number, confirmed, with the charity's officers and returns beneath it; a
    director's namesake charity officer near by name with the reason; a
    charity start's returns newest first, dated 'period to'; a template that
    still names `charities` as not held loads and its memo says the register
    is published."""
    out = []
    # a company (a charitable trust board with no director, where one exists) reaches its charity by business number, confirmed, and the charity's officers
    nz = [x["nzbn"] for x in db.rows(conn, "select ch.nzbn from pub.charities ch where ch.nzbn is not null and ch.status = 'Registered' "
                                           "and exists (select 1 from pub.charity_officers o where o.charity_key = ch.key and o.ended_on is null) order by ch.key limit 300")]
    got = (db.rows(conn, "select c.key from pub.companies c where c.nzbn = any(%s) and c.in_latest and not exists (select 1 from pub.directors d where d.entity_key = c.key) "
                         "order by c.key limit 1", (nz,)) or db.rows(conn, "select c.key from pub.companies c where c.nzbn = any(%s) and c.in_latest order by c.key limit 1", (nz,))) if nz else []
    if got:
        ref = f"companies:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        ch = _items(r, "charities")
        if not ch or ch[0]["grade"] != "confirmed" or ch[0].get("rule") != "official-number" or ch[0]["via"] != ref:
            out.append(f"{ref}: the company's charity is not listed confirmed by business number via the company ({[(c['grade'], c.get('rule')) for c in ch]})")
        else:
            officers = [it for it in _items(r, "charity_officers") if it["via"] == ch[0]["ref"]]
            if not officers or any(it["grade"] != "confirmed" for it in officers):
                out.append(f"{ref}: the charity's officers are not listed confirmed beneath it ({len(officers)} listed)")
            if any("disqualified as the register states it" not in it["statement"] for it in officers):
                out.append(f"{ref}: an officer's statement does not carry the register's disqualified mark")
        sec = [s for s in r["sections"] if s["name"] == "charities"]
        if not sec or not sec[0]["items"] or sec[0]["items"][0]["view"] != "charities":
            out.append(f"{ref}: the charities section does not lead with the charity")
    else:
        out.append("no registered charity with current officers carries a business number of a company in the latest file: the number-join route cannot be checked")
    # a director named as a charity officer reaches the officer row, near by name with the reason
    names = [x["full_name"] for x in db.rows(conn, "select full_name from pub.charity_officers where length(full_name) > 20 and ended_on is null "
                                                   "and not coalesce(suppressed, false) order by key limit 300")]
    got = db.rows(conn, "select d.key, d.full_name from pub.directors d where d.full_name = any(%s) and d.in_latest and not coalesce(d.suppressed, false) order by d.key limit 1", (names,)) if names else []
    if got:
        ref = f"companies:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        named = [it for it in _items(r, "charity_officers") if cat.fold(it["row"].get("full_name") or "") == cat.fold(got[0]["full_name"])]
        same = [it for it in named if it.get("rule") == "same-name"]
        if not named:
            out.append(f"{ref}: a charity officer of the director's name is not listed")
        elif any(it["grade"] != "near" for it in named):   # by name, or through the person's own charity: near either way, no link joins the register yet
            out.append(f"{ref}: a charity officer of the director's name is listed confirmed, and no link rule joins the register yet")
        elif not all("matched to the subject by name" in (it.get("reason") or "") and it["via"] == ref for it in same):
            out.append(f"{ref}: a charity officer matched by name is not near with the by-name reason, via the subject's row")
        elif not same and not any(it.get("via", "").startswith("charities:") for it in named):
            out.append(f"{ref}: a charity officer of the director's name is listed by neither name nor the person's own charity")
    else:
        out.append("no director carries a current charity officer's name: the by-name route cannot be checked")
    # a charity start lists its officers and its returns, newest first, each return dated 'period to'
    got = db.rows(conn, "select ch.key from pub.charities ch where (select count(*) from pub.charity_returns r where r.charity_key = ch.key) between 2 and 20 "
                        "and exists (select 1 from pub.charity_officers o where o.charity_key = ch.key) order by ch.key limit 1")
    if got:
        ref = f"charities:{got[0]['key']}"
        r = build.build(conn, ref, subject, held)
        rets = [it for it in _items(r, "charity_returns") if it["via"] == ref]
        offs = [it for it in _items(r, "charity_officers") if it["via"] == ref]
        if not rets or not offs:
            out.append(f"{ref}: a charity start lists {len(rets)} returns and {len(offs)} officers")
        elif not all("period to" in it["dates"]["text"] and it["grade"] == "confirmed" for it in rets):
            out.append(f"{ref}: a return is not dated 'period to' and confirmed: {rets[0]['dates']['text']!r}")
        elif [it["dates"]["on"] for it in rets] != sorted((it["dates"]["on"] for it in rets), reverse=True):
            out.append(f"{ref}: the returns are not newest first")
        out += [f"{ref}: {p}" for p in r["problems"]]
        out += cited_rows_exist(conn, r)
    else:
        out.append("no charity with two to twenty returns and an officer: the charity-start route cannot be checked")
    # a template that still names `charities` as not held loads, and its memo says the register is published and not read
    t = tpl.Template("check-superseded", "check", "0", "check", "", subject.reads,
                     (tpl.Section("a", "A", ("companies",), not_held=("courts",)),), depth=1, superseded_not_held=(("charities", "charities"),))
    got = db.rows(conn, "select key from pub.companies where in_latest order by key limit 1")
    if got:
        ref = f"companies:{got[0]['key']}"
        text = memo.text(build.build(conn, ref, t, held))
        if "names as not held a register that is published" not in text or "Charities register" not in text:
            out.append(f"{ref}: the memo of a template naming charities as not held does not say the register is published")
        if "Charities register and officers" in text:
            out.append(f"{ref}: the memo still lists the Charities register among the registers not held")
    for name, folder in tpl.folders().items():
        tt = tpl.load(folder)
        if any(key == "charities" for key, _ in tt.superseded_not_held) and {"charities", "charity_officers"} & tt.views:
            out.append(f"template {name}: reads the charities views and still names charities as not held")
    # an officer's near link: a director a near link (name alone) joins to another director row, and nothing confirmed: from the company
    # start, the other row's company is listed under officers, near, with the link's rule and reason after the officer's
    links = db.rows(conn, "select l.row_a, l.row_b, l.rule from pub.links l where l.grade = 'near' and l.row_a like 'companies:%%/director/%%' "
                          "and l.row_b like 'companies:%%/director/%%' order by l.row_a limit 60")
    pick = None
    for l in links:
        d = db.rows(conn, "select key, entity_key from pub.directors where key = %s and in_latest and not coalesce(suppressed, false)", (l["row_a"].split(":", 1)[1],))
        o = db.rows(conn, "select entity_key from pub.directors where key = %s and in_latest and ended_on is null", (l["row_b"].split(":", 1)[1],))
        if d and o and o[0]["entity_key"] != d[0]["entity_key"]:
            pick = (d[0]["entity_key"], l["row_a"], l["row_b"], o[0]["entity_key"], l["rule"])
            break
    if pick:
        start, officer, other, other_co, rule = pick
        ref = f"companies:{start}"
        r = build.build(conn, ref, subject, held)
        got = [it for it in _items(r) if it.get("near_link") and it.get("through") == officer]
        co = [it for it in got if it["ref"] == f"companies:{other_co}"]
        if not co:
            out.append(f"{ref}: the company a near link of the director's reaches ({other_co}, {rule}) is not listed under the officers reach")
        elif not (co[0]["grade"] == "near" and co[0]["rule"] == rule and "and the officer's own link to this row is near: " in (co[0].get("reason") or "")
                  and "reached through a person on the subject" in co[0]["reason"].split("and the officer's own link")[0]):
            out.append(f"{ref}: the near-linked company is not near with the officer's reason first and the link's rule and reason after ({co[0]['rule']}, {co[0].get('reason')!r})")
        if "the officer's own link to this row is near" not in memo.text(r):
            out.append(f"{ref}: the memo does not say the row came by the officer's near link")
    else:
        out.append("no near link between two current directors of different companies among the first sixty: the officer-near-link route cannot be checked")
    # the chain reads the companies above: a holder of record whose own row has a current director (and a notice where one exists) lists them, marked above
    cands = db.rows(conn, "select s.entity_key as k, s.name from pub.shareholders s where s.in_latest and s.shareholder_type = 'company' "
                          "and (select count(*) from pub.companies c where c.name = s.name) = 1 order by s.key limit 40")
    got = []
    for c in cands:
        above = db.rows(conn, "select c.key from pub.companies c where c.name = %s and exists (select 1 from pub.directors d where d.entity_key = c.key and d.in_latest and d.ended_on is null)",
                        (c["name"],))
        if above:
            got.append({"k": c["k"], "above": above[0]["key"]})
            if db.rows(conn, "select 1 from pub.gazette_liquidations where register_key = %s limit 1", (above[0]["key"],)):
                got.insert(0, got.pop())
                break
    if got:
        ref = f"companies:{got[0]['k']}"
        r = build.build(conn, ref, subject, held)
        above = [it for it in _items(r) if it.get("above")]
        directors = [it for it in above if it["view"] == "directors" and it["via"] == f"companies:{got[0]['above']}"]
        if not directors:
            out.append(f"{ref}: the current directors of the company above ({got[0]['above']}) are not listed")
        elif not all(it["grade"] == "near" and it["depth"] == 1 and it["rule"] == "chain" and "name only" in (it.get("reason") or "") for it in directors):
            out.append(f"{ref}: a director above is not near with the chain company's reason at its depth ({directors[0].get('reason')!r})")
        elif any(not walk.current_role(it["row"]) for it in directors):
            out.append(f"{ref}: an ended director of the company above is listed as current")
        n_notices = db.rows(conn, "select count(*) as n from pub.gazette_liquidations where register_key = %s", (got[0]["above"],))[0]["n"]
        if n_notices and not [it for it in above if it["view"] == "gazette_liquidations"]:
            out.append(f"{ref}: the {n_notices} liquidation notice(s) on the company above are not listed")
        if r["walk"]["chain"].get("above_directors", 0) < 1 or "on the companies above" not in memo.text(r):
            out.append(f"{ref}: the memo does not count what was read on the companies above ({r['walk']['chain']})")
    else:
        out.append("no company holder of record resolved by a unique name whose own row has a current director: the companies-above route cannot be checked")
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
    for sv in search.searched_views():
        if sv.name in held:
            cols = {r["column_name"] for r in db.rows(conn, "select column_name from information_schema.columns where table_schema = 'pub' and table_name = %s", (sv.name,))}
            for c in sorted((set(sv.search) | set(sv.numbers) | {sv.default_order}) - cols):
                out.append(f"{sv.name}: the name search reads `{c}`, which pub.{sv.name} does not carry")
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
    out += routes_3(conn, subject, held)
    out += routes_4(conn, subject, held)
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
    # 11. the start page's name search
    if company_key:
        name = db.rows(conn, "select name from pub.companies where key = %s", (company_key,))
        if name and name[0]["name"]:
            out += search_route(name[0]["name"])
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


REF_WORDING = re.compile(r"register:key|as the board names", re.I)


def _get(base: str, path: str) -> tuple:
    try:
        with urllib.request.urlopen(base + path, timeout=120) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def search_route(term: str) -> list:
    """11. A name search on the page's own server (a passing port on the
    loopback): 200, no row-reference wording, rows listed as report links,
    and the first link a memo that says where it starts. Names nothing in
    what it returns but the route."""
    from products.report import server
    out = []
    httpd = server.Server(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        status, body = _get(base, "/?" + urllib.parse.urlencode({"q": term}))
        if status != 200:
            return [f"the start page's search for a known company's name answered {status}"]
        if REF_WORDING.search(body):
            out.append("the start page's search still shows row-reference wording")
        links = [htmllib.unescape(h) for h in re.findall(r'<li><a href="(/report/[^"]+)"', body)]
        if not links:
            return out + ["the start page's search for a known company's name lists no report link"]
        status, page = _get(base, links[0])
        if status != 200:
            out.append(f"the search's first report link answered {status}")
        elif "This report starts from" not in page or "<h3>Citations</h3>" not in page:
            out.append("the search's first report link does not render a memo that says where it starts")
        elif REF_WORDING.search(page):
            out.append("the memo page shows row-reference wording")
    finally:
        httpd.shutdown()
        httpd.server_close()
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
