"""The connections pane's settings (Arthur, 10 November 2026; rulings 158 and 159): the types and the base configuration
declared in connections.toml, the address they live in, what a setting takes out of the walk and what it leaves, and,
on the real tables, the base configuration's effect on a party, a liquidator, a trustee company and an ordinary
director (docs/research/step-9-connections-pane.md)."""
import datetime as dt

import pytest

from products.report import build, catalogue as cat, connections as C, db, stage1, template as tpl, walk

TODAY = dt.date(2026, 11, 10)


def _it(ref, view, via=None, through=None, row=None, dates=None):
    return {"ref": ref, "view": view, "via": via, "through": through, "row": row or {}, "dates": dates or {}, "kind": "person",
            "flags": [], "grade": "confirmed"}


# ── the declared table ──────────────────────────────────────────────────────

def test_every_type_names_known_views_once_and_every_variable_is_declared():
    c = C.config()
    seen = set()
    for t in c["types"]:
        assert t["views"] and all(v in cat.BY_NAME for v in t["views"])
        assert not (set(t["views"]) & seen)
        seen |= set(t["views"])
        assert all(v in c["variables"] for v in t["variables"])
    for name, v in c["variables"].items():
        assert v["default"] in {k for k, _ in v["choices"]}, name


def test_the_follow_views_are_all_role_types_with_the_role_variables():
    for view in stage1.FOLLOW_VIEWS:
        t = C.config()["by_view"][view]
        assert set(C.ROLE_VARS[:2]) <= set(C.variables_of(t)), view


def test_a_view_no_type_names_takes_its_register():
    assert C.type_of({"view": "directors"}) == "director"
    assert C.type_of({"view": "hansard_speeches"}) == "register:hansard"
    assert C.words_of("register:hansard") == cat.REGISTER_NAME["hansard"]


def test_the_base_configuration_by_the_kind_of_subject():
    party = C.subject_kind("parties", "parties:ec-party/1994-12-02/x", "The New Zealand National Party")
    assert party["subject"] == "party"
    b = C.base(party)
    assert (b["donation"]["order"], b["donation"]["top"], b["donation"]["years"]) == ("size", "10", "3")
    liq = C.subject_kind("company_insolvencies", "companies:companies/1/insolvency/a#appointee", "A PERSON")
    assert liq["subject"] == "liquidator" and C.base(liq)["insolvency"]["show"] is False
    assert C.subject_kind("company_insolvencies", "companies:companies/1/insolvency/a#company", "X LIMITED") is None
    tr = C.subject_kind("companies", "companies:companies/1", "HODDLE TRUSTEE COMPANY LIMITED")
    assert tr["subject"] == "trustee" and C.base(tr)["director"]["follow"] == "no" and tr.get("gap")
    assert C.subject_kind("companies", "companies:companies/1", "CUSTODIANSHIP HOLDINGS LIMITED") is None   # whole words
    assert C.subject_kind("directors", "companies:companies/1/director/a", "ANN ROE") is None
    plain = C.base(None)
    assert all(s["show"] for s in plain.values()) and plain["donation"]["top"] == "all" and plain["director"]["follow"] == "yes"


def test_the_settings_live_in_the_address_and_come_back_from_it():
    party = C.subject_kind("parties", "parties:p", "A Party")
    s = C.from_query({"c.donation.top": "25", "c.donation.order": "recency", "c.director.when": "nonsense"}, party)
    assert s["donation"]["top"] == "25" and s["donation"]["order"] == "recency" and s["donation"]["years"] == "3"
    assert s["director"]["when"] == "past"                       # a value not among the choices is ignored
    back = C.from_query(dict(C.to_query(s)), party)
    assert {k: v for k, v in back.items() if not k.startswith("_")} == s
    sent = C.from_query({"c": "1", "c.director": "on", "c.register:hansard": "on"}, None)   # the form sent: no tick is off
    assert sent["director"]["show"] and not sent["shareholder"]["show"] and C.shown(sent, "register:hansard")
    assert not C.shown(sent, "register:courts") and C.shown(C.base(None), "register:courts")


# ── what a setting takes out of the walk ───────────────────────────────────

def _walk():
    start = _it("companies:companies/1", "companies")
    return {"start": start, "members": [],
            "roles": [_it("companies:companies/1/director/a", "directors", via=start["ref"], row={"in_latest": True}),
                      _it("companies:companies/1/director/b", "directors", via=start["ref"], row={"in_latest": False, "ended_on": "2019-01-01"})],
            "officers": [_it("companies:companies/2/director/a2", "directors", via="companies:companies/1/director/a",
                             through="companies:companies/1/director/a", row={"in_latest": True}),
                         _it("companies:companies/2", "companies", via="companies:companies/2/director/a2", through="companies:companies/1/director/a"),
                         _it("companies:companies/3/director/b3", "directors", via="companies:companies/1/director/b",
                             through="companies:companies/1/director/b", row={"in_latest": True}),
                         _it("companies:companies/3/insolvency/q#company", "company_insolvencies", via="companies:companies/3/director/b3")],
            "beside": [_it("companies:companies/2/director/z", "directors", via="companies:companies/2", through="companies:companies/1/director/a")],
            "entities": [start], "confirmed": [], "near": [], "pointing": [], "second": [], "named": [], "office": [], "chain": [], "stage1": []}


def _refs(w):
    return {it["ref"] for b in C.PRUNED_BUCKETS for it in w.get(b, []) if "ref" in it}


def test_base_takes_nothing_out():
    w = _walk()
    before = _refs(w)
    assert C.prune(w, C.base(None), today=TODAY) == {} and _refs(w) == before


def test_not_followed_keeps_the_rows_and_takes_out_what_was_reached_through_them():
    w = _walk()
    s = C.base(None)
    s["director"]["follow"] = "no"
    counts = C.prune(w, s, today=TODAY)
    assert _refs(w) == {"companies:companies/1", "companies:companies/1/director/a", "companies:companies/1/director/b"}
    assert counts == {"director": 3, "company": 1, "insolvency": 1}


def test_a_type_off_takes_out_its_rows_and_everything_reached_through_them_but_never_the_subject():
    w = _walk()
    s = C.base(None)
    s["company"]["show"] = False
    C.prune(w, s, today=TODAY)
    assert _refs(w) == {"companies:companies/1", "companies:companies/1/director/a", "companies:companies/1/director/b",
                        "companies:companies/2/director/a2", "companies:companies/3/director/b3", "companies:companies/3/insolvency/q#company"}   # the company the officer sits on goes, and the director beside on it


def test_current_only_and_since_take_out_ended_roles():
    w = _walk()
    s = C.base(None)
    s["director"]["when"] = "current"
    C.prune(w, s, today=TODAY)
    assert "companies:companies/1/director/b" not in _refs(w) and "companies:companies/1/director/a" in _refs(w)
    # and what was reached through the ended role goes with it, two steps on
    assert not {"companies:companies/3/director/b3", "companies:companies/3/insolvency/q#company"} & _refs(w)
    w = _walk()
    s = C.base(None)
    s["director"]["since"] = "5"
    C.prune(w, s, today=TODAY)
    assert "companies:companies/1/director/b" not in _refs(w)      # ended 2019, before November 2021
    s["director"]["since"] = "10"
    w = _walk()
    C.prune(w, s, today=TODAY)
    assert "companies:companies/1/director/b" in _refs(w)


def test_the_first_stage_is_told_what_not_to_walk_on_from():
    s = C.base(None)
    keep = C.role_keeps(s, TODAY)
    assert keep("directors", {"in_latest": True}) and not keep("directors", {"in_latest": False})
    s["director"]["when"] = "followed"
    assert C.role_keeps(s, TODAY)("directors", {"in_latest": False, "ended_on": "2024-01-01"})
    s["director"]["since"] = "1"
    assert not C.role_keeps(s, TODAY)("directors", {"in_latest": False, "ended_on": "2024-01-01"})
    s["director"]["follow"] = "no"
    s["land"]["show"] = False
    assert {"directors", "company_lookup_roles", "linz_titles"} <= C.stop_views(s) and "directors" not in C.hidden_views(s)


def test_donations_by_size_or_recency_top_n_within_the_period():
    def d(ref, amount, year):
        return _it(ref, "party_return_donors", row={"amount": amount, "year": year}, dates={"year": year})
    items = [d("a", 100, 2025), d("b", 900, 2020), d("c", 500, 2024), d("e", 50, 2026), d("f", 700, 2023)]
    kept, out = C.donation_keep(items, {"order": "size", "top": "2", "years": "3"}, TODAY)
    assert [x["ref"] for x in kept] == ["f", "c"] and {x["ref"] for x in out} == {"a", "b", "e"}
    kept, _ = C.donation_keep(items, {"order": "recency", "top": "2", "years": "all"}, TODAY)
    assert [x["ref"] for x in kept] == ["e", "a"]
    kept, out = C.donation_keep(items, {"order": "size", "top": "all", "years": "all"}, TODAY)
    assert len(kept) == 5 and not out


def test_the_pane_lists_types_counts_and_controls():
    report = {"subject": {"ref": "s"}, "sections": [{"items": [{"ref": "x", "view": "directors"}, {"ref": "y", "view": "hansard_speeches"}]}],
              "connections": {"settings": C.base(None), "set_aside": {"company": 3}}}
    got = {r["key"]: r for r in C.pane_rows(report)}
    assert set(got) == {"director", "company", "register:hansard"}
    assert got["director"]["listed"] == 1 and got["company"]["set_aside"] == 3
    assert [v[0] for v in got["director"]["variables"]] == ["when", "since", "follow"] and got["register:hansard"]["variables"] == []


# ── on the real tables ──────────────────────────────────────────────────────

def _build(conn, ref, qs=None, held=None):
    kind, s = C.settings_for(conn, ref, qs or {})
    t = tpl.by_name("one")
    return kind, build.build(conn, ref, t, held=held, walker=C.walker(s, kind, stage=t.stage))


def _listed(report):
    return [it for s in report["sections"] for it in s["items"]]


@pytest.mark.slow
def test_a_party_lists_its_top_10_donations_by_size_over_three_years():
    with db.read_connect() as conn:
        p = db.rows(conn, "select party_key as key from pub.party_return_donors where replaced_by is null group by 1 "
                          "having count(*) filter (where year >= extract(year from now())::int - 3) > 20 order by count(*) desc limit 1")
        assert p, "no party with twenty donations in three years"
        ref = "parties:" + p[0]["key"]
        want = [r["key"] for r in db.rows(conn, "select key from pub.party_return_donors where party_key = %s and replaced_by is null "
                                                "and year >= extract(year from now())::int - 3 order by amount desc nulls last, year desc, key limit 10",
                                          (p[0]["key"],))]
        kind, r = _build(conn, ref)
        assert kind["subject"] == "party" and not r["problems"]
        got = [it["ref"].split(":", 1)[1] for it in _listed(r) if it["view"] == "party_return_donors"]
        assert got == want                                            # listed in the order chosen, the largest first
        line = r["hub_lines"][0]
        assert line["subject"] and line["text"].startswith("a hub: a party:") and "top 10 by size" in line["text"]
        _, r25 = _build(conn, ref, {"c.donation.top": "25", "c.donation.order": "recency"})
        years = [it["row"]["year"] for it in _listed(r25) if it["view"] == "party_return_donors"]
        assert len(years) == 25 and years == sorted(years, reverse=True)


@pytest.mark.slow
def test_a_liquidator_s_appointments_are_counted_not_listed():
    with db.read_connect() as conn:
        g = db.rows(conn, "select group_id from pub.groups where group_id like 'companies:%%#appointee' group by 1 "
                          "having count(*) between 200 and 2000 order by 1 limit 1")
        assert g, "no liquidator group of 200 to 2000 appointments"
        ref = g[0]["group_id"]
        kind, r = _build(conn, ref)
        assert kind["subject"] == "liquidator" and not r["problems"]
        assert not [it for it in _listed(r) if it["view"] == "company_insolvencies" and it["ref"] != r["subject"]["ref"]]
        assert r["connections"]["set_aside"].get("insolvency", 0) > 100
        size = db.rows(conn, "select count(*) as n from pub.groups where group_id = %s", (ref,))[0]["n"]
        assert r["hub_lines"][0]["count"] == size and f"{size:,} appointments" in r["hub_lines"][0]["text"]
        _, shown = _build(conn, ref, {"c": "1", **{f"c.{t['key']}": "on" for t in C.config()["types"]}})
        assert len([it for it in _listed(shown) if it["view"] == "company_insolvencies"]) > 100    # ticked, they come back


@pytest.mark.slow
def test_a_trustee_company_lists_its_directors_and_follows_none_of_their_other_companies():
    with db.read_connect() as conn:
        c = db.rows(conn, """
            select d.entity_key as key from pub.directors d join pub.companies c on c.key = d.entity_key
            where d.in_latest and d.ended_on is null and c.status = 'Registered' and c.name ~* '\\mtrustees?\\M'
              and 'companies:' || d.key in (select row_key from pub.groups where group_id in (
                  select group_id from pub.groups where row_key like 'companies:companies/%%/director/%%' group by 1 having count(*) > 300 limit 20))
            group by 1 order by 1 limit 5""")
        assert c, "no trustee company with a director of more than 300 companies"
        cut = 0
        for row in c:
            ref = "companies:" + row["key"]
            kind, r = _build(conn, ref)
            assert kind["subject"] == "trustee" and not r["problems"]
            mine = {it["ref"] for it in _listed(r) if it["view"] == "directors" and it.get("via") == ref}
            assert mine, ref
            far = [it for it in _listed(r) if it.get("through") in mine or (it.get("via") in mine)]
            assert not far, (ref, far[:2])
            line = r["hub_lines"][0]
            assert line["kind"] == "base-trustee" and line.get("gap") and line["count"] > 300
            cut += r["connections"]["set_aside"].get("director", 0) + r["connections"]["set_aside"].get("company", 0)
        assert cut, "none of the trustee companies' directors sits anywhere else"


@pytest.mark.slow
def test_a_family_trust_s_trustee_company_is_no_hub_and_is_followed_as_before():
    with db.read_connect() as conn:
        c = db.rows(conn, "select c.key from pub.companies c join pub.directors d on d.entity_key = c.key and d.in_latest and d.ended_on is null "
                          "where c.name ~* '\\mtrustees?\\M' and c.status = 'Registered' group by 1 having count(*) between 1 and 3 "
                          "order by 1 limit 40")
        for row in c:
            ref = "companies:" + row["key"]
            if C.most_directorships(conn, row["key"]) < 10:
                kind, _ = C.settings_for(conn, ref, {})
                assert kind is None, ref
                return
        pytest.fail("no trustee company of forty whose directors hold fewer than ten directorships")


@pytest.mark.slow
def test_an_ordinary_director_s_report_is_as_before():
    with db.read_connect() as conn:
        g = db.rows(conn, """
            select min(g.row_key) filter (where g.row_key like '%%/director/%%') as ref from pub.groups g
            where g.group_id in (select group_id from pub.groups where row_key in (
                select 'companies:' || key from pub.directors where in_latest and ended_on is null and not coalesce(suppressed, false)
                order by key limit 3000))
            group by g.group_id having count(*) filter (where g.row_key like '%%/director/%%') between 4 and 30 order by 1 limit 1""")
        ref = g[0]["ref"]
        held = db.pub_views(conn)
        before = build.build(conn, ref, tpl.by_name("one"), held=held)
        kind, after = _build(conn, ref, held=held)
        assert kind is None
        assert sorted(it["ref"] for it in _listed(before)) == sorted(it["ref"] for it in _listed(after))
        assert after["connections"]["set_aside"] == {}
        _, cut = _build(conn, ref, {"c.director.follow": "no"}, held=held)
        assert len(_listed(cut)) <= len(_listed(after))
        mine = {m["ref"] for m in after.get("members", [])} | {ref}
        directors = {it["ref"] for it in _listed(cut) if it["view"] == "directors" and it["ref"] not in mine}
        assert not [it for it in _listed(cut) if it.get("through") in directors]
        far = lambda r: sum(x["entities"] for x in r["walk"]["stage1"]["levels"] if x["hop"] >= 3)
        assert far(after) == 0 or far(cut) < far(after)               # the first stage itself did not walk on from them


@pytest.mark.slow
def test_a_hub_the_web_met_is_said_on_the_result():
    with db.read_connect() as conn:
        ref = "companies:" + db.rows(conn, """
            select entity_key as key from pub.shareholders where in_latest group by 1
            having count(*) between 70 and 120 order by 1 limit 1""")[0]["key"]
        _, r = _build(conn, ref)
        lines = r["hub_lines"]
        assert lines and lines[0]["subject"] and lines[0]["ref"] == ref and "a hub:" in lines[0]["text"]
        from products.report import memo
        html = memo.html_body(r)
        assert "Hubs not followed" in html and html.index("Hubs not followed") < html.index("<h3>Flags</h3>")
        assert "HUBS NOT FOLLOWED" in memo.text(r)
