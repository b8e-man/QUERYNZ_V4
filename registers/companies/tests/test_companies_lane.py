"""The companies lane's tests (step 4.1). The reading's rules are tested on
small exports shaped like the real one (every name and address invented);
the filled sample is tested against the row contract, the windows, the catch
log, the private table and the published views. No model is called."""
import datetime as dt
import gzip
import json
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.companies import check, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "companies")
JUL, AUG = "companies-2026-07", "companies-2026-08"
SHA = "0" * 64


def _export(part, lines, runs=None):
    runs = runs or {JUL: {"entities": 0, "directors": 0, "shareholders": 0},
                    AUG: {"entities": 0, "directors": 0, "shareholders": 0}}
    head = {"t": "export", "part": part, "files": [JUL, AUG], "runs": runs, "aux_rows": {}}
    return gzip.compress(("\n".join(json.dumps(l, sort_keys=True) for l in [head] + lines) + "\n").encode())


def _runs(part, jul, aug):
    z = {"entities": 0, "directors": 0, "shareholders": 0}
    return {JUL: {**z, part: jul}, AUG: {**z, part: aug}}


def _director(nzbn, first, last, start, files, **kw):
    return {"t": "director", "nzbn": nzbn, "number": "1", "first_name": first, "middle_names": None,
            "last_name": last, "full_name": f"{first} {last}", "role_type": "DIRECTOR", "appointed_on": start,
            "files": files, "last_file": files[-1] if files else "nzbn_api_backfill", "suppressed": False,
            "old_id": "x", **kw}


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


# --- entities -----------------------------------------------------------------------

def test_an_entity_is_keyed_by_its_nzbn_else_its_register_number_and_dates_are_as_filed():
    lines = [
        {"t": "entity", "register": "companies", "nzbn": "9429000000001", "number": "11", "name": "Example Limited",
         "type": "LTD", "status": "Registered", "registered_on": "1868-03-02", "removed_on": None,
         "files": [JUL, AUG], "last_file": AUG, "old_id": "a"},
        {"t": "entity", "register": "other_incorporated", "nzbn": "9429000000002", "number": "22",
         "name": "Example Society", "type": "Incorporated Society", "status": "Registered",
         "registered_on": "02/03/1951", "removed_on": "", "files": [], "last_file": AUG, "in_latest": True,
         "extra": {"incorporated_societies_act": "2022"}},
        {"t": "entity", "register": "retirement_village", "nzbn": None, "number": "77", "name": "Example Village",
         "registered_on": "45-08-2014", "files": [], "last_file": AUG, "in_latest": True},
    ]
    r = read.read("entities", _export("entities", lines, _runs("entities", 1, 1)), SHA)
    keys = {x["key"]: x["filed"] for x in r.rows["entities"]}
    assert set(keys) == {"companies/9429000000001", "companies/9429000000002", "companies/retirement_village/77"}
    assert keys["companies/9429000000001"]["registered_on"] == "1868-03-02"
    assert keys["companies/9429000000002"]["registered_on"] == "1951-03-02"
    assert keys["companies/retirement_village/77"]["registered_on"] is None
    assert any("not a real day" in w for _, _, w, _ in r.set_aside)


def test_an_entity_a_later_file_changed_keeps_its_earlier_state():
    line = {"t": "entity", "register": "companies", "nzbn": "9429000000001", "number": "11", "name": "New Name Limited",
            "type": "LTD", "status": "Registered", "registered_on": "2020-01-01", "files": [JUL, AUG],
            "last_file": AUG, "earlier": [{"name": "Old Name Limited", "status": "Registered", "type": "LTD",
                                           "registered_on": "2020-01-01", "removed_on": None, "file": JUL}]}
    r = read.read("entities", _export("entities", [line], _runs("entities", 1, 1)), SHA)
    (s,) = r.rows["entity_states"]
    assert s["key"] == "companies/9429000000001/in/" + JUL and s["filed"]["name"] == "Old Name Limited"


# --- roles ----------------------------------------------------------------------------

def test_a_role_s_window_is_the_files_it_was_in_and_it_carries_no_end_date():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG]),
             _director("9429000000001", "Ben", "Baker", "2018-01-01", [JUL]),
             _director("9429000000001", "Cy", "Carter", "2026-07-20", [AUG])]
    r = read.read("directors", _export("directors", lines, _runs("directors", 2, 2)), SHA)
    by = {x["filed"]["full_name"]: x["filed"] for x in r.rows["directors"]}
    assert (by["Ann Able"]["first_file"], by["Ann Able"]["last_file"], by["Ann Able"]["in_latest"]) == (JUL, AUG, True)
    assert (by["Ben Baker"]["last_file"], by["Ben Baker"]["in_latest"]) == (JUL, False)
    assert all(f["ended_on"] is None for f in by.values())
    assert r.set_aside == []


def test_the_key_is_the_company_and_the_filed_content_and_is_the_same_on_every_read():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG])]
    data = _export("directors", lines, _runs("directors", 1, 1))
    one, two = read.read("directors", data, SHA), read.read("directors", data, SHA)
    assert one.rows["directors"][0]["key"] == two.rows["directors"][0]["key"]
    assert one.rows["directors"][0]["key"].startswith("companies/9429000000001/director/")


def test_lines_the_old_loader_folded_are_one_counted_catch_log_line_and_api_rows_are_set_aside():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG]),
             _director("9429000000001", "Dee", "Doe", "2001-01-01", []),
             _director("9429000000001", None, None, "2001-01-01", [AUG], full_name=None)]
    r = read.read("directors", _export("directors", lines, _runs("directors", 3, 2)), SHA)
    assert len(r.rows["directors"]) == 1
    reasons = {w: c for _, _, w, c in r.set_aside}
    assert any("not a monthly file" in w for w in reasons) and any("no name" in w for w in reasons)
    folded = [(i, c) for i, _, w, c in r.set_aside if "folded" in w]
    assert folded == [(f"{SHA}/{JUL}", 2)]


def test_a_file_with_more_rows_than_it_had_lines_does_not_reconcile():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG])]
    with pytest.raises(AssertionError):
        read.read("directors", _export("directors", lines, _runs("directors", 0, 1)), SHA)


def test_a_shareholding_is_keyed_on_holder_shares_and_status():
    sh = {"t": "shareholder", "nzbn": "9429000000001", "number": "1", "shareholder_type": "individual",
          "full_name": "Ann Able", "shareholder_entity_name": None, "shareholder_nzbn": None,
          "allocation_type": "active", "suppressed": False, "old_id": "x"}
    lines = [{**sh, "shares": "100.0000", "files": [JUL], "last_file": JUL},
             {**sh, "shares": "150", "files": [AUG], "last_file": AUG}]
    r = read.read("shareholders", _export("shareholders", lines, _runs("shareholders", 1, 1)), SHA)
    a, b = r.rows["shareholders"]
    assert a["key"] != b["key"] and a["filed"]["shares"] == "100" and not a["filed"]["in_latest"]


# --- registered offices ----------------------------------------------------------------

def test_a_registered_office_repeated_exactly_is_one_row_and_an_empty_one_is_set_aside():
    ro = {"t": "registered_office", "register": "companies", "nzbn": "9429000000001", "number": None,
          "start": "01/02/2020", "care_of": None, "line_1": "1 Example Street", "line_2": "Exampletown",
          "line_3": None, "line_4": None, "postcode": "1010", "country": "NZ", "last_file": AUG}
    lines = [{**ro, "in_latest": False, "last_file": JUL}, {**ro, "in_latest": True},
             {**ro, "line_1": "2 Sample Road", "start": "05/06/2015", "in_latest": False, "last_file": JUL},
             {**ro, "line_1": None, "line_2": None, "postcode": None, "start": None, "in_latest": True}]
    r = read.read("addresses", _export("addresses", lines), SHA)
    rows = r.rows["registered_offices"]
    assert len(rows) == 2 and len(r.set_aside) == 2
    current = [x for x in rows if x["filed"]["in_latest"]]
    assert len(current) == 1 and current[0]["filed"]["started_on"] == "2020-02-01"
    assert current[0]["key"].startswith("companies/9429000000001/registered-office/2020-02-01/")


def test_the_sample_filter_matches_the_nzbn_and_the_number_only_where_there_is_no_nzbn():
    lines = [{"t": "entity", "register": "companies", "nzbn": "9429000000001", "number": "77", "name": "A",
              "files": [AUG], "last_file": AUG},
             {"t": "entity", "register": "retirement_village", "nzbn": None, "number": "77", "name": "B",
              "files": [], "last_file": AUG, "in_latest": True}]
    r = read.read("entities", _export("entities", lines, _runs("entities", 0, 1)), SHA, only={"77"})
    assert [x["filed"]["name"] for x in r.rows["entities"]] == ["B"]


# --- the outside check -------------------------------------------------------------------

def test_the_check_compares_the_last_quarter_before_the_cut_and_each_month():
    months = {k: v for k, v in check.MONTHS.items()}
    live = dict(check.QUARTERS)
    f = check.figures(live, months, "2026-08-02")
    assert f["quarters"][-1][0] == "2026-06-30" and f["months"][-1][0] == (2026, 7)
    assert check.failed(f) == []
    live["2026-06-30"] = int(check.QUARTERS["2026-06-30"] * 1.01)
    assert any("2026-06-30" in w for w in check.failed(check.figures(live, months, "2026-08-02")))
    months[(2026, 3)] = (6000, 1528)
    assert any("2026-03" in w for w in check.failed(check.figures(dict(check.QUARTERS), months, "2026-08-02")))
    assert check.failed(check.figures({}, {}, "2020-01-01"))


# --- the filled sample ---------------------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_companies"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        t = {n: q(f"SELECT * FROM {schema}.companies_{n} ORDER BY key") for n in
             ("entities", "entity_states", "directors", "shareholders", "registered_offices")}
        yield {"schema": schema, "conn": conn, **t,
               "aside": q(f"SELECT * FROM {schema}.companies_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.companies_residential_addresses")}


def _ent(filled, k):
    return next(e for e in filled["entities"] if e["key"] == k)


def test_every_listed_entity_is_held_once(filled):
    from registers.companies import sample as S
    listed = S.keys_of(sample.read_list(os.path.join(LANE, "sample.list")))
    held = {e["nzbn"] or e["number"] for e in filled["entities"]}
    assert held == listed - {"9429053756381"}          # the one whose company the entity file does not name
    assert any(s["nzbn"] == "9429053756381" for s in filled["shareholders"])


def test_each_case_reads_as_its_comment_says(filled):
    assert _ent(filled, "companies/9429052986758")["last_file"] == JUL
    assert _ent(filled, "companies/9429053782670")["first_file"] == AUG
    assert _ent(filled, "companies/9429032000856")["registered_on"] < dt.date(1900, 1, 1)
    assert _ent(filled, "companies/9429049224986")["removed_on"] is not None
    assert _ent(filled, "companies/retirement_village/2634153")["nzbn"] is None
    assert any(s["entity_key"] == "companies/9429039628022" for s in filled["entity_states"])
    roles = [d for d in filled["directors"] if d["nzbn"] == "9429052976568"]
    assert any(not d["in_latest"] and d["last_file"] == JUL for d in roles)
    assert any(d["first_file"] == AUG for d in roles)
    held = [s for s in filled["shareholders"] if s["nzbn"] == "9429051738563"]
    assert any(not s["in_latest"] for s in held) and any(s["first_file"] == AUG for s in held)
    offices = [o for o in filled["registered_offices"] if o["entity_key"] == "companies/9429033434155"]
    assert sum(o["in_latest"] for o in offices) == 1 and len(offices) > 1
    assert not [o for o in filled["registered_offices"] if o["entity_key"] == "companies/9429041902967"]


def test_no_role_carries_an_end_date_the_file_does_not_state(filled):
    assert all(d["ended_on"] is None for d in filled["directors"])


def test_the_catch_log_holds_what_was_set_aside(filled):
    reasons = [a["reason"] for a in filled["aside"]]
    assert any("not a monthly file" in r for r in reasons)
    assert any("no name" in r for r in reasons)
    assert any("no address in it" in r for r in reasons)


def test_no_residential_address_is_held_or_published(filled):
    assert filled["private"] == []                      # the monthly files carry none
    for t in ("directors", "shareholders"):
        assert not set(filled[t][0]) & {"address", "line_1", "postcode", "residential_address"}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("entities", "entity_states", "directors", "shareholders", "registered_offices"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version",
                                     "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            assert rowcontract.validate(row, today) == [], (t, r["key"])


def test_the_published_views_build_and_carry_no_private_column(filled):
    from registers.companies import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.companies_pub_"))
    counts = {v: conn.execute(f"SELECT count(*) FROM {schema}.companies_pub_{v}").fetchone()[0]
              for v in ("companies", "directors", "shareholders", "company_addresses")}
    cols = {v: [d[0] for d in conn.execute(f"SELECT * FROM {schema}.companies_pub_{v} LIMIT 0").description]
            for v in ("companies", "directors", "shareholders", "company_addresses")}
    conn.rollback()
    assert counts["companies"] == len(filled["entities"]) and counts["directors"] == len(filled["directors"])
    assert not any("old_id" in c for c in cols.values())
    assert not set(cols["directors"]) & set(rowcontract.FORBIDDEN_COLUMNS)


def test_the_outside_check_measures_the_lane_s_own_table(filled):
    from registers.companies import load as L
    f = check.measure(filled["conn"], L.table(filled["schema"], "entities", True))
    assert f["cut"] >= "2026-07-01" and f["quarters"] and f["months"]
