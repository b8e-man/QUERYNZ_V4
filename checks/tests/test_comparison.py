"""The comparison with the frozen site: figures read the same way from both
sides, differences with no tolerance on money, causes that need a card,
the day record, the ledger and the board item. Fixtures only; the one test
on the real folders is slow and skipped where they are absent."""
import datetime as dt
import json
import os

import pytest

from checks import comparison as C
from checks import comparison_figures as F

NOW = dt.datetime(2026, 10, 20, 8, 45, tzinfo=dt.timezone(dt.timedelta(hours=13)))


# ── values ────────────────────────────────────────────────────────────────────

def test_money_is_whole_cents_with_no_float_noise():
    assert F.cents(0.1 + 0.2) == 30 and F.cents("783830.17") == 78383017 and F.cents(None) is None
    assert F.cents(317287.83) - F.cents(317287.13) == 70


def test_none_and_no_entry_are_the_same_fact_but_a_zero_declared_total_is_not():
    assert F.same("party/X/declared/2026", None, F.ABSENT)
    assert not F.same("party/X/declared/2021", 0, F.ABSENT)
    assert F.same("party/X/named/2024", 0, F.ABSENT) and F.same("public_money/allocated", F.ABSENT, 0)
    assert not F.same("by_year/2023", 1637500, F.ABSENT)
    assert not F.same("race/2020/elected", "edmonds barbara", None)


def test_person_key_folds_the_three_ways_a_name_is_written():
    assert F.person_key("Barbara Edmonds") == F.person_key("Barbara Faith EDMONDS") == F.person_key("EDMONDS, Barbara") == "edmonds barbara"
    assert F.person_key("Dieuwe de Boer") == F.person_key("DE BOER, Dieuwe") == "boer dieuwe"
    assert F.person_key("Hon Judith Collins KC") == F.person_key("Judith COLLINS")
    assert F.person_key("Tim van de Molen") == F.person_key("Tim VAN DE MOLEN")


def test_a_name_segment_with_a_residence_word_is_withheld_from_the_record():
    assert C.withhold("donors/A Person, Sunny Retirement Village/total") == "donors/[name withheld: residence fragment]/total"
    assert C.withhold("data/donor/a-person-sunny-retirement-village-1a2b3c4d.json") == "data/donor/[name withheld: residence fragment]"
    assert C.withhold("donors/Village Green Trust/total") == "donors/Village Green Trust/total" and C.withhold(123) == 123


def test_slug_and_spelling_keys():
    assert F.slug_of_path("data/subject/person/aaron-stallard-8936a9e5.json") == "aaron-stallard"
    assert F.spelling_key("3EYES Construction Ltd") == F.spelling_key("3Eyes Construction Limited")


# ── the party card on both sides ─────────────────────────────────────────────

OLD_PARTY = {"party": "ACT New Zealand", "seats": 11,
             "declared_by_year": {"2019": 332025.0, "2020": 1227121.15},
             "disclosed_by_year": {"2023": 1864060.12},
             "public_money": {"allocated": 519303.0, "spent": 511708.82, "by_year": {"2020": 150755.0}, "spent_by_year": {"2020": 150740.17}},
             "window": {"total": 1559146.15, "named": 513910.0, "over_line": 513910.0,
                        "series": [{"year": 2019, "basis": "declared", "total": 332025.0, "named": 188000.0},
                                   {"year": 2020, "basis": "declared", "total": 1227121.15, "named": 325910.0},
                                   {"year": 2026, "basis": "disclosed", "total": 100.0, "named": 100.0}],
                        "by_cycle": {"2020": {"total": 1559146.15, "named": 513910.0, "over_line": 513910.0}}}}
NEW_PARTY = {"party": "ACT New Zealand", "seats": {"electorate": 2, "list": 9, "total": 11},
             "declared_by_year": {"2019": 332025.0, "2020": 1227121.15, "2026": None},
             "named_by_year": {"2019": 188000.0, "2020": 325910.0, "2026": None},
             "disclosed_by_year": {"2023": 1864060.12},
             "public_money": {"allocated": 519303.0, "spent": 511708.82, "by_year": {"2020": 150755.0}, "spent_by_year": {"2020": 150740.17}},
             "total_window": 1559146.15, "named_window": 513910.0, "over_line_window": 513910.0,
             "races": {"2020": {"total": 1559146.15, "named": 513910.0, "over_line": 513910.0}}}


def test_the_same_party_read_from_both_shapes_gives_the_same_figures():
    old, new = F.party_card_old(OLD_PARTY), F.party_card_new(NEW_PARTY)
    assert old["declared/2019"] == new["declared/2019"] == 33202500
    assert old["named/2020"] == new["named/2020"] == 32591000
    assert old["seats"] == new["seats"] == 11
    assert "named/2026" not in old and {k for k in old if k not in new} == set()
    diffs = [k for k in set(old) | set(new) if not F.same(k, old.get(k, F.ABSENT), new.get(k, F.ABSENT))]
    assert diffs == []


def test_a_part_a_year_not_read_is_a_named_figure_of_none():
    new = dict(NEW_PARTY, named_by_year={"2019": 188000.0, "2020": None})
    f = F.party_card_new(new)
    assert f["named/2020"] is None and f["named/2019"] == 18800000


# ── differences of one file ───────────────────────────────────────────────────

def home_docs(new_amount=1227121.15):
    old = {"parties": [OLD_PARTY], "totals": {"party_spend": 21364169.97}, "donors": [{"name": "A", "total": 100.0}],
           "recent_disclosures": {"n": 1, "total": 50000.0, "rows": [{"party": "P", "donor": "D", "amount": 50000.0}]},
           "generated_at": "x", "press": [1]}
    np = json.loads(json.dumps(NEW_PARTY))
    np["declared_by_year"]["2020"] = new_amount
    new = {"parties": [np], "totals": {"party_spend": 21364169.97}, "donors": [{"name": "A", "total": 100.0}],
           "recent_disclosures": {"n": 1, "total": 50000.0, "rows": [{"party": "P", "donor": "D", "amount": 50000.0}]},
           "generated_at": "y", "basis": "b"}
    return old, new


def test_identical_figures_are_no_difference_and_one_cent_is():
    old, new = home_docs()
    diffs = {d["figure"]: d for d in C.diff_file("home", "data/home.json", "data/home.json", old, new)}
    assert set(diffs) == {"section/press"}, diffs
    old, new = home_docs(1227121.16)
    diffs = {d["figure"]: d for d in C.diff_file("home", "data/home.json", "data/home.json", old, new)}
    assert diffs["party/ACT New Zealand/declared/2020"]["old"] == 122712115
    assert diffs["party/ACT New Zealand/declared/2020"]["new"] == 122712116


def test_rows_differ_as_multisets_and_name_what_each_side_lacks():
    old = {"subject": "P", "party_window": {"headline": {}}, "donations_received": [
        {"year": 2019, "amount": 160000.0, "line_kind": "name"}]}
    new = {"subject": "P", "card": {}, "donations_received": [
        {"year": 2019, "amount": 160000.0}, {"year": 2019, "amount": 28000.0}]}
    d = {x["figure"]: x for x in C.diff_file("subject", "data/subject/party/p-1.json", "data/subject/party/p-1.json", old, new)}
    assert d["rows/2019"]["old_only"] == [] and d["rows/2019"]["new_only"] == [2800000]


def test_a_file_one_side_lacks_is_one_difference():
    assert C.diff_file("donor", "data/donor/x-1.json", None, {"name": "x"}, None) == [{"figure": "file", "old": "present", "new": F.ABSENT}]


def test_person_pages_match_by_slug_when_only_the_hash_differs():
    old = {"data/subject/person/aaron-stallard-066cb445.json": "subject", "data/subject/person/only-old-1.json": "subject"}
    new = {"data/subject/person/aaron-stallard-8936a9e5.json": "subject", "data/subject/person/only-new-2.json": "subject"}
    m = C.match_files(old, new)
    assert ("subject", "data/subject/person/aaron-stallard-066cb445.json", "data/subject/person/aaron-stallard-8936a9e5.json") in m
    assert ("subject", "data/subject/person/only-old-1.json", None) in m and ("subject", None, "data/subject/person/only-new-2.json") in m


# ── causes ────────────────────────────────────────────────────────────────────

def ctx():
    c = C.context.__wrapped__() if hasattr(C.context, "__wrapped__") else None
    return {"unread_party_years": {("ACT New Zealand", "2017")}, "donor_causes": {}, "new_rows": {}, "old_rows": {},
            "old_parties": {"ACT New Zealand"}, "left_out_party_years": set(), "unheld_party_years": set(),
            "new_people": {}, "no_result": set(), "old_people": {}, "unread_names": {("act new zealand", "2017")},
            "left_out_names": set(), "unheld_names": set(), "new_multi": {}, "race_causes": {},
            "withheld_expenses": set()}


def d(kind, figure, old, new, **more):
    x = {"kind": kind, "path": "p", "figure": figure, "old": old, "new": new, "old_doc": {}, "new_doc": {}, "file_diffs": []}
    x.update(more)
    x["file_diffs"].append(x)
    return x


def test_a_not_held_electorate_figure_is_the_candidate_returns_cause():
    assert C.assign(d("electorate", "race/2020/declared_total", 9660523, F.NOT_HELD), ctx()) == "candidate-returns-not-held"


def test_an_unread_party_year_is_the_part_a_cause_and_a_disclosed_figure_is_not():
    assert C.assign(d("home", "party/ACT New Zealand/named/2017", 39090000, None), ctx()) == "part-a-rows-not-read"
    assert C.assign(d("home", "party/ACT New Zealand/disclosed/2017", F.ABSENT, 28620000), ctx()) == "frozen-reads-the-2023-regime-only"


def test_a_window_figure_follows_a_differing_year_on_the_same_page():
    year = d("home", "party/ACT New Zealand/named/2017", 39090000, None)
    agg = d("home", "party/ACT New Zealand/window/named", 945958715, 625474149, file_diffs=year["file_diffs"])
    assert C.assign(agg, ctx()) == "named-in-2026-is-disclosed" or C.assign(agg, ctx()) == "aggregate-of-a-differing-part"
    agg2 = d("home", "party/ACT New Zealand/races/2023/total", 1, 2, file_diffs=year["file_diffs"])
    assert C.assign(agg2, ctx()) == "aggregate-of-a-differing-part"


def test_a_difference_no_rule_knows_is_uncarded():
    assert C.assign(d("home", "party/ACT New Zealand/declared/2023", 1, 2), ctx()) is None


def test_every_cause_names_a_card_a_side_and_an_owner():
    for c in C.CAUSES:
        if c["card"] is None:
            continue
        assert c["right"] in ("frozen", "new", "neither"), c["id"]
        assert c["owner"] and c["card"]


# ── a day, the ledger, the board item ─────────────────────────────────────────

def write(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f)


def make_pair(tmp_path, new_amount=1227121.15, listing="2026-10-20T0620"):
    old_live = tmp_path / "old"
    versions = old_live / "var" / "pi-snapshot" / "v"
    frozen = versions / "2026-10-20T0620"
    site = tmp_path / "site"
    new = site / "v" / "2026-10-20T1134"
    old_home, new_home = home_docs(new_amount)
    write(str(frozen), "data/home.json", old_home)
    write(str(frozen), "data/cite/cdon-1-aaaaaaaa.json", {"evidence_text": "x"})
    write(str(new), "data/home.json", new_home)
    write(str(new), "data/cite/disclosures-x-bbbbbbbb.json", {"evidence_text": "y"})
    write(str(new), "SNAPSHOT.json", {"listing": {"version": listing}})
    rel = old_live / "var" / "pi-snapshot" / "RELEASES.jsonl"
    with open(rel, "w") as f:
        f.write(json.dumps({"action": "publish", "version": "2026-10-20T0620"}) + "\n")
    cards = tmp_path / "cards"
    cards.mkdir()
    for c in C.CAUSES:
        if c["card"]:
            (cards / f"{c['card']}.md").write_text("# c\nkind: finding\nstate: open\n")
    return str(versions), str(rel), str(site), str(cards), str(tmp_path / "state")


def test_a_day_is_recorded_grouped_by_cause_and_the_ledger_counts_clean_days(tmp_path):
    versions, releases, site, cards, state = make_pair(tmp_path)
    day = C.run(state_dir=state, site=site, versions=versions, releases=releases, now=NOW, cards_dir=cards)
    assert day["ok"] and day["frozen"] == "2026-10-20T0620" and day["new"] == "2026-10-20T1134"
    assert set(day["by_cause"]) == {"cite-key", "section-not-in-template"}
    assert day["uncarded"] == 0 and day["explained"] and not day["clean"]   # a section the template lacks: the new side is short
    rows = C.ledger(state)
    assert len(rows) == 1 and rows[0]["clean"] is False and C.streak(rows) == 0
    assert os.path.exists(os.path.join(state, "days", "2026-10-20T0620.json"))
    r = C.check(now=NOW, state_dir=state)
    assert r["ok"] and "0 uncarded" in r["items"][0]["detail"] and "0 clean day" in r["items"][1]["detail"]


def test_a_difference_without_a_card_makes_the_day_red(tmp_path):
    versions, releases, site, cards, state = make_pair(tmp_path, new_amount=1227121.16)
    day = C.run(state_dir=state, site=site, versions=versions, releases=releases, now=NOW, cards_dir=cards)
    assert day["uncarded"] == 1 and not day["explained"]
    r = C.check(now=NOW, state_dir=state)
    assert not r["ok"] and "1 uncarded" in r["items"][0]["detail"]


def test_a_missing_card_file_makes_its_differences_uncarded(tmp_path):
    versions, releases, site, cards, state = make_pair(tmp_path)
    os.remove(os.path.join(cards, "page-sections-the-template-does-not-carry.md"))
    day = C.run(state_dir=state, site=site, versions=versions, releases=releases, now=NOW, cards_dir=cards)
    assert day["uncarded"] == 1


def test_no_rebuilt_version_from_todays_listing_is_a_failed_day(tmp_path):
    versions, releases, site, cards, state = make_pair(tmp_path, listing="2026-10-19T0619")
    day = C.run(state_dir=state, site=site, versions=versions, releases=releases, now=NOW, cards_dir=cards)
    assert not day["ok"] and "no rebuilt version built from listing 2026-10-20T0620" in day["note"]
    r = C.check(now=NOW, state_dir=state)
    assert not r["ok"] and "no rebuilt version" in r["items"][0]["detail"]


def test_the_board_item_is_red_when_the_comparison_never_ran_or_is_stale(tmp_path):
    r = C.check(now=NOW, state_dir=str(tmp_path))
    assert not r["ok"] and "never run" in r["items"][0]["detail"]
    versions, releases, site, cards, state = make_pair(tmp_path)
    C.run(state_dir=state, site=site, versions=versions, releases=releases, now=NOW - dt.timedelta(hours=30), cards_dir=cards)
    r = C.check(now=NOW, state_dir=state)
    assert not r["ok"] and "30 h ago" in r["items"][0]["detail"]


def test_seven_clean_days_in_a_row_is_the_pass_and_a_dirty_day_resets_it():
    rows = [{"clean": True}] * 7
    assert C.streak(rows) == 7 >= C.PASS_DAYS
    assert C.streak(rows + [{"clean": False}, {"clean": True}]) == 1


@pytest.mark.slow
def test_the_real_pair_runs_and_every_cause_found_has_a_card():
    """On the box: today's frozen version against the rebuilt one; every
    cause the rules assign must have its card in cards/, else the day
    cannot be explained. Skipped where the folders are absent."""
    p = C.pair()
    if not p["frozen"] or not p["new"]:
        pytest.skip("no pair on this box")
    r = C.compare(os.path.join(C.FROZEN_VERSIONS, p["frozen"]), os.path.join(C.NEW_SITE, "v", p["new"]))
    missing = [cid for cid, c in r["by_cause"].items() if cid != "uncarded" and C.card_state(c["card"]) in (None, "dropped")]
    assert missing == [], missing
    assert r["differences"] > 0 and sum(v["figures"] for v in r["kinds"].values()) > 10000
