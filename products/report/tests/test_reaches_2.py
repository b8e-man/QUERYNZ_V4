"""The fix-report-2 reaches, on canned links and rows: an officer's near
links are listed beside the confirmed, each graded near with the officer's
reason and then the link's own, carrying the link's rule (card
the-officers-reach-does-not-list-an-officers-near-links); the chain lists,
on each company above, the notices pointing at it and its current
directors, with the company's grade, marked above at its depth (card
the-chain-reach-reads-nothing-on-the-companies-above); the memo prints
both."""
import datetime as dt

from products.report import build, catalogue as cat, memo, template as tpl, walk
from products.report.tests.test_reaches import canned_walk, item

START = "companies:companies/1"
SU = "companies:companies/1/director/su"          # the start's one director
ROBERTON = "companies:companies/2"                # a company a near link (name-only) joins SU to
ROBERTON_D = "companies:companies/2/director/x"
CONFIRMED_CO = "companies:companies/3"            # a company in SU's confirmed group
CONFIRMED_D = "companies:companies/3/director/y"

ROWS = {
    SU: ("directors", {"key": "companies/1/director/su", "entity_key": "companies/1", "full_name": "Wenfeng SU", "role_type": "Director", "appointed_on": dt.date(2020, 1, 1),
                       "ended_on": None, "in_latest": True, "suppressed": False}),
    ROBERTON_D: ("directors", {"key": "companies/2/director/x", "entity_key": "companies/2", "full_name": "Wenfeng SU", "role_type": "Director", "appointed_on": dt.date(2018, 1, 1),
                               "ended_on": None, "in_latest": True, "suppressed": False}),
    CONFIRMED_D: ("directors", {"key": "companies/3/director/y", "entity_key": "companies/3", "full_name": "Wenfeng Jun SU", "role_type": "Director", "appointed_on": dt.date(2019, 1, 1),
                                "ended_on": None, "in_latest": True, "suppressed": False}),
    START: ("companies", {"key": "companies/1", "name": "GORING DEVELOPMENT LIMITED", "status": "Registered", "entity_type": "LTD", "nzbn": "1"}),
    ROBERTON: ("companies", {"key": "companies/2", "name": "ROBERTON LIMITED", "status": "In Liquidation", "entity_type": "LTD", "nzbn": "2"}),
    CONFIRMED_CO: ("companies", {"key": "companies/3", "name": "KERVIL DEVELOPMENT LIMITED", "status": "Registered", "entity_type": "LTD", "nzbn": "3"}),
}
LIQ = {"key": "gazette/liq/1", "company": "ROBERTON LIMITED", "shape": "liquidation", "appointed_by": "the court", "appointed_on": dt.date(2024, 5, 1),
       "published_on": dt.date(2024, 5, 3), "register_key": "companies/2", "notice": "n1"}


def canned(monkeypatch, near_links=True):
    monkeypatch.setattr(walk, "resolve", lambda conn, ref, cache: (cat.BY_NAME[ROWS[ref][0]], ROWS[ref][1]) if ref in ROWS else None)
    monkeypatch.setattr(walk, "group_of", lambda conn, ref: {"built": True, "why": "", "group_id": 7, "contested": False, "settings": None,
                                                           "rows": [SU, CONFIRMED_D] if ref == SU else [ref], "size": 2, "omitted": 0})
    monkeypatch.setattr(walk, "links_of", lambda conn, refs: {"built": True, "omitted": 0,
                                                            "confirmed": [{"this": SU, "other": CONFIRMED_D, "rule": "full-name@1", "evidence": None, "grade": "confirmed", "reason": None, "watch": [], "decision": None}],
                                                            "near": [{"this": SU, "other": ROBERTON_D, "rule": "name-only@1", "evidence": {"name": "wenfeng su"}, "grade": "near",
                                                                      "reason": "the names match and nothing else is shared", "watch": [], "decision": None}] if near_links else []})
    monkeypatch.setattr(walk.rows, "entity_of", lambda conn, v, r: (cat.BY_NAME["companies"], ROWS["companies:" + r["entity_key"]][1]) if v.entity and r.get("entity_key") else (None, None))
    monkeypatch.setattr(walk, "pointing_at", lambda conn, ev, e, allowed, skipped: [walk.item(cat.BY_NAME["gazette_liquidations"], LIQ, "ROBERTON LIMITED", via=ROBERTON)] if e["key"] == "companies/2" else [])


def test_an_officers_near_links_are_listed_beside_the_confirmed_each_with_the_links_rule_and_reason(monkeypatch):
    canned(monkeypatch)
    allowed = {"companies", "directors", "gazette_liquidations"}
    su = walk.item(cat.BY_NAME["directors"], ROWS[SU][1], "GORING DEVELOPMENT LIMITED", via=START)
    items, followed, past, links_omitted = walk.follow_officers(None, START, [su], allowed, [], {})
    assert followed == 1 and past == 0 and links_omitted == 0
    by_ref = {it["ref"]: it for it in items if "omitted" not in it}
    # the confirmed group's company, as before: near through the officer, rule through-officer
    assert by_ref[CONFIRMED_CO]["rule"] == "through-officer" and by_ref[CONFIRMED_CO]["reason"] == walk.NEAR_THROUGH_OFFICER.format(who="Wenfeng SU")
    assert not by_ref[CONFIRMED_CO].get("near_link")
    # the near-linked director row, its company and the liquidation on it: near, the officer's reason first and the link's own after, the link's rule
    for ref in (ROBERTON_D, ROBERTON, "gazette:gazette/liq/1"):
        it = by_ref[ref]
        assert it["grade"] == "near" and it["rule"] == "name-only@1" and it["near_link"] and it["through"] == SU and it["depth"] == 1, ref
        assert it["reason"] == walk.NEAR_OFFICER_LINK.format(officer=walk.NEAR_THROUGH_OFFICER.format(who="Wenfeng SU"), link="the names match and nothing else is shared")
    assert by_ref[ROBERTON_D]["evidence"] == {"name": "wenfeng su"} and by_ref[ROBERTON_D]["via"] == SU and by_ref[ROBERTON]["via"] == ROBERTON_D
    assert [it["ref"] for it in items].index(CONFIRMED_CO) < [it["ref"] for it in items].index(ROBERTON)
    # without the near links the namesake's company is not there: the change is what lists it
    canned(monkeypatch, near_links=False)
    items2, *_ = walk.follow_officers(None, START, [su], allowed, [], {})
    assert ROBERTON not in {it["ref"] for it in items2 if "omitted" not in it} and CONFIRMED_CO in {it["ref"] for it in items2 if "omitted" not in it}
    # the memo says the row came by the officer's near link
    w = canned_walk()
    w["officers"] = items
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: w)
    r = build.build(None, START, tpl.by_name("subject"), held={v.name for v in cat.VIEWS})
    text = memo.text(r)
    assert "ROBERTON LIMITED: In Liquidation LTD" in text and "the officer's own link to this row is near" in text and "rule name-only@1" in text
    assert r["problems"] == []


class ChainDB:
    def __init__(self):
        self.calls = []

    def rows(self, conn, sql, params=()):
        self.calls.append(sql)
        if "from pub.shareholders where entity_key = any" in sql:
            keys = params[0]
            out = []
            if "companies/1" in keys:   # the start's holder: a company, by name
                out.append({"key": "companies/1/shareholder/h", "entity_key": "companies/1", "name": "PARENT HOLDINGS LIMITED", "shareholder_type": "company",
                            "shares": 100, "allocation_status": "active", "holder_nzbn": None, "in_latest": True, "first_file": "f1", "last_file": "f2", "suppressed": False, "rn": 1, "total": 1})
            return out
        if "from pub.companies where name = any" in sql:
            return [{"key": "companies/9", "name": "PARENT HOLDINGS LIMITED", "status": "In Liquidation", "entity_type": "LTD", "nzbn": "9", "registered_on": dt.date(2015, 1, 1), "removed_on": None}]
        if "from pub.companies where nzbn" in sql:
            return []
        if "from pub.directors" in sql:
            return [{"key": "companies/9/director/p", "entity_key": "companies/9", "full_name": "Pat PARENT", "role_type": "Director", "appointed_on": dt.date(2016, 1, 1),
                     "ended_on": None, "in_latest": True, "suppressed": False, "total": 2},
                    {"key": "companies/9/director/q", "entity_key": "companies/9", "full_name": "Quinn GONE", "role_type": "Director", "appointed_on": dt.date(2016, 1, 1),
                     "ended_on": dt.date(2020, 1, 1), "in_latest": True, "suppressed": False, "total": 2}]
        raise AssertionError(sql)


def test_the_chain_reads_the_notices_and_current_directors_on_the_companies_above(monkeypatch):
    fake = ChainDB()
    monkeypatch.setattr(walk.db, "rows", fake.rows)
    liq = dict(LIQ, company="PARENT HOLDINGS LIMITED", register_key="companies/9", key="gazette/liq/9")
    monkeypatch.setattr(walk, "pointing_at", lambda conn, ev, e, allowed, skipped: [walk.item(cat.BY_NAME["gazette_liquidations"], liq, "PARENT HOLDINGS LIMITED", via="companies:companies/9")]
                        if e["key"] == "companies/9" else [])
    start = {"key": "companies/1", "name": "CHILD LIMITED", "status": "Registered", "entity_type": "LTD", "nzbn": "1"}
    allowed = {"companies", "shareholders", "directors", "gazette_liquidations"}
    items, stats = walk.chain(None, "companies:companies/1", start, allowed, [], 2)
    by_ref = {it["ref"]: it for it in items if "omitted" not in it and "chain_note" not in it}
    parent = by_ref["companies:companies/9"]
    assert parent["grade"] == "near" and parent["depth"] == 1 and "name only" in parent["reason"]
    notice, director = by_ref["gazette:gazette/liq/9"], by_ref["companies:companies/9/director/p"]
    for it in (notice, director):
        assert it["above"] and it["depth"] == 1 and it["through"] == "companies:companies/9" and it["via"] == "companies:companies/9"
        assert it["grade"] == "near" and it["reason"] == parent["reason"] and it["rule"] == "chain"
    assert "companies:companies/9/director/q" not in by_ref   # an ended role is not a current director
    assert stats["above_notices"] == 1 and stats["above_directors"] == 1 and stats["companies"] == 1
    # with no directors view allowed the directors are skipped and said so
    skipped = []
    items2, stats2 = walk.chain(None, "companies:companies/1", start, allowed - {"directors"}, skipped, 2)
    assert "directors" in skipped and stats2["above_directors"] == 0 and stats2["above_notices"] == 1
    # the memo: a section naming the chain bucket and the views lists them, each on a company one up
    w = canned_walk()
    w["chain"], w["chain_stats"] = items, stats
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: w)
    r = build.build(None, "companies:companies/1", tpl.by_name("subject"), held={v.name for v in cat.VIEWS})
    text = memo.text(r)
    assert "Pat PARENT: Director of PARENT HOLDINGS LIMITED" in text and "on a company 1 up the chain (companies:companies/9)" in text
    assert "liquidation, appointed by the court" in text and "on the companies above, 1 Gazette notices and 1 current directors read" in text
    assert r["problems"] == []
    html = memo.html_body(r)
    assert "on a company 1 up the chain" in html
