"""Step 9 tranche 6 (ruling 157): the one report's first stage. Fast: the
template on disk is what make.py writes, the constants are the ones the
research file asks Arthur about, a role row's currency. Slow, on the real
tables: no near link is followed, the web's first hop is the subject's own
current organisations, a hub limit stops the web where it should, and the
built report breaks no presentation rule."""
import os

import pytest

from products.report import build, db, stage1, template as tpl, walk
from products.report.templates.one import make

RESEARCH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "research", "step-9-stage1-depth.md")
NAME_RULES = ("name-only", "full-name", "owner-full-name", "organisation-name", "company-name", "filed-name")


def test_template_on_disk_is_what_make_writes():
    with open(os.path.join(os.path.dirname(make.__file__), "template.toml"), encoding="utf-8") as f:
        assert f.read() == make.render(), "run products/report/templates/one/make.py"


def test_the_constants_are_the_ones_put_to_arthur():
    with open(RESEARCH, encoding="utf-8") as f:
        text = f.read()
    assert f"`HOPS = {stage1.HOPS}`" in text
    assert f"`HUB_PEOPLE = HUB_ENTITIES = {stage1.HUB_PEOPLE}`" in text and stage1.HUB_PEOPLE == stage1.HUB_ENTITIES


def test_buckets_agree():
    assert tuple(walk.BUCKETS) == tpl.BUCKETS and "stage1" in walk.BUCKETS


def test_a_role_is_current_as_its_view_files_it():
    assert stage1.current("directors", {"in_latest": True, "ended_on": None})
    assert not stage1.current("directors", {"in_latest": True, "ended_on": "2020-01-01"})
    assert not stage1.current("directors", {"in_latest": False})
    assert not stage1.current("shareholders", {"in_latest": False})
    assert not stage1.current("limited_partnership_partners", {"current": False})
    assert not stage1.current("society_officers", {"ended_on": "2021-01-01"})
    assert stage1.current("charity_officers", {})


def test_entity_refs():
    assert stage1.is_entity_ref("companies:companies/9429000000001")
    assert not stage1.is_entity_ref("companies:companies/9429000000001/director/abc")
    assert not stage1.is_entity_ref("parties:The Party")


# ── on the real tables ──────────────────────────────────────────────────────

def _common_name_director(conn):
    """A current director row whose name the links lane joins to many namesakes: found at run time, never fixed."""
    got = db.rows(conn, """
        select l.row_a as ref from pub.links l join pub.directors d on 'companies:' || d.key = l.row_a
        where l.rule = 'name-only@1' and d.in_latest and d.ended_on is null and not coalesce(d.suppressed, false)
        group by l.row_a having count(*) between 5 and 60 order by l.row_a limit 1""")
    assert got, "no director row with namesakes"
    return got[0]["ref"]


def _many_company_director(conn):
    """A group with four to thirty current director rows, from the first rows of the directors file: found at run time."""
    got = db.rows(conn, """
        select g.group_id, min(g.row_key) filter (where g.row_key like '%%/director/%%') as ref from pub.groups g
        where g.group_id in (select group_id from pub.groups where row_key in (
            select 'companies:' || key from pub.directors where in_latest and ended_on is null and not coalesce(suppressed, false)
            order by key limit 3000))
        group by 1 having count(*) filter (where g.row_key like '%%/director/%%') between 4 and 30 order by 1 limit 1""")
    assert got, "no group with four to thirty director rows"
    return got[0]


@pytest.mark.slow
def test_no_near_link_is_followed_and_the_set_aside_is_counted():
    with db.read_connect() as conn:
        ref = _common_name_director(conn)
        held = db.pub_views(conn)
        diag = build.build(conn, ref, tpl.by_name("diagnostic"), held=held)
        one = build.build(conn, ref, tpl.by_name("one"), held=held)
    def by_name(r):
        return [it for s in r["sections"] for it in s["items"] if it["grade"] == "near" and (it.get("rule") or "").startswith(NAME_RULES)]
    assert by_name(diag), "the diagnostic lists no namesake for a row the links join to namesakes: the instrument sees nothing"
    assert not by_name(one), "the first stage listed a row reached by a name"
    # every near row is near by the design's through-people default or a contested group, never by a near link or a name
    allowed = (walk.NEAR_THROUGH_PEOPLE, walk.NEAR_CONTESTED_GROUP, walk.NEAR_THROUGH_OFFICER.split("{")[0], walk.NEAR_BESIDE[0].split("{")[0],
               stage1.NEAR_STAGE_ORG.split("{")[0], walk.NEAR_THROUGH_NEAR.format(reason=walk.NEAR_CONTESTED_GROUP))
    bad = [(it["ref"], it["reason"]) for s in one["sections"] for it in s["items"]
           if it["grade"] == "near" and not (it.get("reason") or "").startswith(allowed)]
    assert not bad, bad[:3]
    st = one["walk"]["stage1"]
    assert st["stage"] == 1 and st["near_set_aside"] >= len({it["ref"] for it in by_name(diag)}) > 0
    assert one["problems"] == [], one["problems"][:5]
    fl = {f["rule"]: f for f in one["flags"]}
    assert fl["namesake-exposure"]["status"] == "fired" and f"{st['near_set_aside']:,}" in fl["namesake-exposure"]["text"]


@pytest.mark.slow
def test_hop_one_is_the_subjects_own_current_companies():
    with db.read_connect() as conn:
        g = _many_company_director(conn)
        own = [r["row_key"] for r in db.rows(conn, "select row_key from pub.groups where group_id = %s", (g["group_id"],))]
        c = stage1.closure(conn, g["ref"], own)
        current = {r["entity_ref"] for r in db.rows(conn, """
            select distinct n.entity_ref from pub.names n join pub.directors d on 'companies:' || d.key = n.ref
            where n.ref = any(%s) and d.in_latest and d.ended_on is null""", (own,))}
        every = {r["entity_ref"] for r in db.rows(conn, "select distinct entity_ref from pub.names where ref = any(%s) and entity_ref is not null",
                                                  (own,))}
        hop1 = {e for e, h in c["entities"].items() if h == 1}
        assert current <= hop1, f"{len(current - hop1)} current director companies missing from hop 1"
        linked = {x for x in hop1 - every}
        conf = db.rows(conn, "select count(*) as n from pub.links where grade = 'confirmed' and (row_a = any(%s) or row_b = any(%s))", (own, own))
        assert not linked or conf[0]["n"] > 0, "hop 1 holds organisations neither a row nor a confirmed link reaches"
        assert c["levels"][0] == {"hop": 1, "entities": len(hop1), "people": 0}
        people2 = {r for r, (h, _) in c["people"].items() if h == 2}
        assert not people2 & set(own), "the subject's own rows were counted as people beside the subject"


@pytest.mark.slow
def test_an_ended_role_is_not_followed():
    """A company the subject's group sits on only through a role that ended (or left the file) is not in hop 1."""
    with db.read_connect() as conn:
        cands = db.rows(conn, """
            select g.group_id from pub.groups g join pub.directors d on d.key = substr(g.row_key, 11)
            where g.row_key like 'companies:%%/director/%%' and g.group_id in (select group_id from pub.groups where row_key in (
                select 'companies:' || key from pub.directors where in_latest and ended_on is null and not coalesce(suppressed, false)
                order by key limit 3000))
            group by 1 having count(*) between 2 and 30 and count(*) filter (where not d.in_latest or d.ended_on is not null) > 0
            order by 1 limit 20""")
        for cand in cands:
            own = [r["row_key"] for r in db.rows(conn, "select row_key from pub.groups where group_id = %s", (cand["group_id"],))]
            rows_ = db.rows(conn, """
                select n.entity_ref, n.ref, (d.key is not null and (not d.in_latest or d.ended_on is not null)) as ended
                from pub.names n left join pub.directors d on 'companies:' || d.key = n.ref where n.ref = any(%s) and n.entity_ref is not null""",
                            (own,))
            linked = {x for l in db.rows(conn, "select row_a, row_b from pub.links where grade = 'confirmed' and (row_a = any(%s) or row_b = any(%s))",
                                         (own, own)) for x in (l["row_a"], l["row_b"])}
            ended_only = {r["entity_ref"] for r in rows_ if r["ended"]} - {r["entity_ref"] for r in rows_ if not r["ended"]} - linked
            if ended_only:
                c = stage1.closure(conn, own[0], own)
                hop1 = {e for e, h in c["entities"].items() if h == 1}
                assert not ended_only & hop1, f"{len(ended_only & hop1)} organisation(s) followed through an ended role"
                return
    pytest.fail("no group among the first twenty has a company held only through an ended role: the instrument has nothing to see")


@pytest.mark.slow
def test_a_hub_limit_stops_the_web():
    with db.read_connect() as conn:
        g = _many_company_director(conn)
        own = [r["row_key"] for r in db.rows(conn, "select row_key from pub.groups where group_id = %s", (g["group_id"],))]
        wide = stage1.closure(conn, g["ref"], own)
        tight = stage1.closure(conn, g["ref"], own, hub_people=1)
    assert wide["people"], "no people at hop 2: the measure has nothing to stop"
    assert len(tight["people"]) < len(wide["people"]) and tight["hubs"], "a hub limit of one person stopped nothing"
    assert {e for e, h in tight["entities"].items() if h == 1} == {e for e, h in wide["entities"].items() if h == 1}, \
        "a hub limit dropped the subject's own organisations"


@pytest.mark.slow
def test_a_company_in_liquidation_reports_its_notice_red_and_loses_it_without():
    with db.read_connect() as conn:
        got = db.rows(conn, """
            select 'companies:' || g.register_key as ref from pub.gazette_liquidations g join pub.companies c on c.key = g.register_key
            where g.register_key is not null and c.status ilike '%%liquidation%%' order by g.key limit 1""")
        assert got
        r = build.build(conn, got[0]["ref"], tpl.by_name("one"))
    fl = {f["rule"]: f for f in r["flags"]}
    assert (fl["insolvency-notices"]["status"], fl["insolvency-notices"]["severity"]) == ("fired", "red")
    notices = [it["ref"] for s in r["sections"] for it in s["items"] if it["view"] == "gazette_liquidations"]
    assert notices and set(notices) & set(fl["insolvency-notices"]["citations"]), "the notice is not what the check rests on"
    assert "undated" not in fl["insolvency-notices"]["text"]
    assert r["problems"] == [], r["problems"][:5]
    from products.report import checks_combined as cc
    for s in r["sections"]:
        s["items"] = [it for it in s["items"] if it["view"] not in cc.NOTICE_VIEWS]
    f = cc.insolvency_notices(r)
    assert f["status"] == "fired" and "undated" in f["text"], "with its notices gone the check still said it saw one"


@pytest.mark.slow
@pytest.mark.parametrize("ref", ["companies:companies/9429041091357/director/3ffe2546fd6d",   # a professional director
                                 "companies:companies/9429038055164",                         # a company with many holders
                                 "societies:societies/9429000014458",
                                 "party_returns:a7e03e19e71030eb088d72b30f8ede131d20c89d2eb31a75148b2c933de2fa45/A/21"])
def test_measured_subjects_build_within_the_limits(ref):
    with db.read_connect() as conn:
        r = build.build(conn, ref, tpl.by_name("one"))
    if not r["found"]:
        pytest.skip(f"{ref} is no longer published")
    st = r["walk"]["stage1"]
    assert r["problems"] == [], r["problems"][:5]
    assert st["listed"] <= stage1.LIST_ROWS
    assert st["depth"] == stage1.HOPS and len([l for l in st["levels"] if l["hop"] <= stage1.HOPS]) <= stage1.HOPS
    assert sum(1 for s in r["sections"] for it in s["items"] if it.get("stage1")) == st["listed"]
