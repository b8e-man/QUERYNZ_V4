"""The societies lane's tests (step 4.1). The reading's rules are tested on
small exports and answers shaped like the real ones (every name invented);
the filled sample is tested against the row contract, the windows, the catch
log, the private table and the published views. No model is called and
nothing is fetched: the gate is given a robots record and a fake transport."""
import datetime as dt
import gzip
import json
import os

import pytest

from support import db, fetchgate, lane, rowcontract, sample
from registers.societies import capture, check, load, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "societies")
SHA = "0" * 64
N1, N2 = "9429000000017", "9429000000024"


def _export(part, lines, counts=None):
    head = {"t": "export", "part": part, "counts": counts or {"rows": len(lines), "current": len(lines), "vanished": 0}}
    return gzip.compress(("\n".join(json.dumps(l, sort_keys=True) for l in [head] + lines) + "\n").encode())


def _officer(nzbn, first, last, start, end=None, status="Active", imported="2026-10-14 02:00:00+13:00", **kw):
    return {"t": "officer", "nzbn": nzbn, "first_name": first, "middle_names": None, "last_name": last,
            "full_name": f"{first} {last}", "role_type": "Officer", "role_status": status, "start_date": start,
            "end_date": end, "unique_identifier": "ABCDEFGHIJKLMNOP", "imported_at": imported, "old_id": "1", **kw}


def _society(nzbn, name, status="registered", vanished=None, file="companies-2026-08", **kw):
    return {"t": "society", "nzbn": nzbn, "incorporation_number": "1", "entity_name": name, "entity_status": status,
            "entity_type": "Incorporated Society", "registration_date": "02/03/1951", "deregistration_date": None,
            "incorporated_societies_act": "2022", "incsoc2022act_reregistration_date": None,
            "charities_register_number": None, "file": file, "vanished_at": vanished, **kw}


def _ask(nzbn, n, ok=True, at="2026-10-14 02:00:00+13:00", note=None):
    return {"t": "ask", "nzbn": nzbn, "asked_at": at, "ok": ok, "officers": n, "entity_type": None, "note": note}


def _answer(nzbn, roles):
    return json.dumps({"nzbn": nzbn, "entityName": "AN EXAMPLE SOCIETY INCORPORATED",
                       "entityStatusDescription": "Registered", "roles": roles}).encode()


def _role(first, last, start, **kw):
    return {"roleType": "officer", "roleStatus": "Active", "startDate": start + "T00:00:00.000+1300",
            "endDate": None, "rolePerson": {"firstName": first, "middleNames": None, "lastName": last},
            "roleAddress": [], "uniqueIdentifier": "ABCDEFGHIJKLMNOP", **kw}


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


# --- societies ------------------------------------------------------------------------

def test_a_society_is_keyed_by_its_nzbn_and_an_earlier_state_is_kept():
    lines = [_society(N1, "OLD NAME INCORPORATED", file="companies-2026-07", vanished="2026-08-16"),
             _society(N1, "NEW NAME INCORPORATED"), _society(N2, "THE EXAMPLE PARTY OF NEW ZEALAND INCORPORATED")]
    r = read.read_export("societies", _export("societies", lines, {"current": 2, "vanished": 1}), SHA)
    by = {x["key"]: x["filed"] for x in r.rows["societies"]}
    assert set(by) == {f"societies/{N1}", f"societies/{N2}"}
    assert by[f"societies/{N1}"]["name"] == "NEW NAME INCORPORATED" and by[f"societies/{N1}"]["registered_on"] == "1951-03-02"
    assert by[f"societies/{N2}"]["party_society"] and not by[f"societies/{N1}"]["party_society"]
    (s,) = r.rows["society_states"]
    assert s["key"] == f"societies/{N1}/in/companies-2026-07" and s["filed"]["name"] == "OLD NAME INCORPORATED"


def test_a_part_that_does_not_match_the_old_table_s_count_raises():
    with pytest.raises(AssertionError, match="old table held"):
        read.read_export("officers", _export("officers", [_officer(N1, "Ann", "Able", "2019-05-01")], {"rows": 2}), SHA)


# --- officers -------------------------------------------------------------------------

def test_an_officer_is_keyed_on_names_and_start_and_the_end_is_the_register_s_own():
    lines = [_officer(N1, "Ann", "Able", "2019-05-01"),
             _officer(N1, "Ann", "Able", "2019-05-01", end="2024-02-03", status="Inactive"),
             _officer(N1, "Bob", "Baker", None)]
    r = read.read_export("officers", _export("officers", lines), SHA)
    keys = sorted(x["key"] for x in r.rows["officers"])
    base = f"societies/{N1}/officer/{read.short(read.officer_content('Ann', None, 'Able', '2019-05-01'))}"
    assert base in keys and base + "/2" in keys and len(keys) == 3
    ended = [x["filed"] for x in r.rows["officers"] if x["filed"]["ended_on"]]
    assert ended == [] or all(e["ended_on"] == "2024-02-03" and e["ended_on_stated"] for e in ended)
    assert all(x["filed"]["first_read_on"] == "2026-10-14" for x in r.rows["officers"])
    again = read.read_export("officers", _export("officers", list(reversed(lines))), SHA)
    assert sorted(x["key"] for x in again.rows["officers"]) == keys


def test_an_ask_note_keeps_no_query_string():
    r = read.read_export("asks", _export("asks", [_ask(N1, 0, ok=False, note="HTTPStatusError: 500 for url "
                                                         "'https://example.test/v5/entities/1?key=secret'\nmore")]), SHA)
    note = r.rows["asks"][0]["filed"]["note"]
    assert "secret" not in note and "more" not in note


def test_officers_reconcile_with_the_last_ask_or_raise():
    offs = read.read_export("officers", _export("officers", [_officer(N1, "Ann", "Able", "2019-05-01"),
                                                             _officer(N2, "Bob", "Baker", "2020-01-01")]), SHA)
    good = read.read_export("asks", _export("asks", [_ask(N1, 1), _ask(N2, 0, ok=False)]), SHA)
    lines, counts = read.reconcile(offs, good)
    assert counts == {"equal": 1, "kept_from_an_earlier_ask": 1} and "kept from an earlier ask" in lines[0][2]
    bad = read.read_export("asks", _export("asks", [_ask(N1, 3), _ask(N2, 1)]), SHA)
    with pytest.raises(AssertionError, match="do not reconcile"):
        read.reconcile(offs, bad)


# --- the register's own answer --------------------------------------------------------

def test_an_answer_names_a_role_as_the_export_does_and_an_address_goes_private_only():
    roles = [_role("Ann", "Able", "2019-05-01", roleAddress=[{"address1": "1 Example Street"}]),
             {"roleType": "officer", "roleEntity": {"entityName": "A BODY LIMITED"}, "rolePerson": None},
             {"roleType": "Director", "rolePerson": {"firstName": "C", "lastName": "D"}}]
    r = read.read_answer(_answer(N1, roles), SHA, "2026-10-20T07:28:04+13:00")
    (o,) = r.rows["officers"]
    assert o["key"] == f"societies/{N1}/officer/{read.short(read.officer_content('Ann', None, 'Able', '2019-05-01'))}"
    assert "Example Street" not in json.dumps(o) and o["filed"]["private_ref"] == o["key"]
    assert r.private == [(o["key"], {"roleAddress": [{"address1": "1 Example Street"}]}, SHA)]
    assert "Example Street" not in json.dumps(r.set_aside) + json.dumps(r.counts)
    assert sorted(w for _, _, w, _ in r.set_aside) == ["a Director role, not an officer",
                                                         "an officer that is a body, not a person: not read yet"]
    assert r.rows["asks"][0]["filed"]["officers"] == 1


def test_an_answer_keeps_the_first_day_a_role_was_read_and_a_dropped_role_keeps_its_last():
    offs = read.read_export("officers", _export("officers", [_officer(N1, "Ann", "Able", "2019-05-01"),
                                                             _officer(N1, "Bob", "Baker", "2018-01-01")]), SHA)
    held = {r["key"]: r for r in offs.rows["officers"]}
    a = read.read_answer(_answer(N1, [_role("Ann", "Able", "2019-05-01")]), "1" * 64, "2026-10-20T07:28:04+13:00")
    assert load.merge_answer(held, a) == {"listed_again": 1, "new": 0}
    ann = next(r for r in held.values() if r["filed"]["first_name"] == "Ann")
    bob = next(r for r in held.values() if r["filed"]["first_name"] == "Bob")
    assert (ann["filed"]["first_read_on"], ann["filed"]["last_read_on"], ann["document"]) == ("2026-10-14", "2026-10-20", "1" * 64)
    assert bob["filed"]["last_read_on"] == "2026-10-14"


# --- the nightly ask ------------------------------------------------------------------

def test_tonight_s_slice_is_the_party_societies_then_the_stalest_seventh():
    socs = [(f"94290000{i:05d}", f"CLUB {i} INCORPORATED", "registered") for i in range(70)]
    socs.append(("9429099999999", "THE EXAMPLE PARTY OF NEW ZEALAND INCORPORATED", "registered"))
    socs.append(("9429099999998", "EXAMPLE PARTY YOUNG MEMBERS INCORPORATED", "registered"))
    asked = {n: "2026-10-1%d" % (i % 7) for i, (n, _, _) in enumerate(socs[:60])}
    tonight = capture.slice_for(socs, asked)
    assert tonight[0] == "9429099999999" and len(tonight) == 11
    assert all(n not in asked for n in tonight[1:])                     # never asked first
    assert "9429099999998" not in tonight                                # not a party: it waits its turn


def _gate(monkeypatch, tmp_path):
    host = fetchgate.host_of(capture.BASE)
    monkeypatch.setitem(fetchgate._ROBOTS, host, fetchgate.Robots(host, "", 404, False, 0.0, "", ""))
    return {"positions_dir": capture.POSITIONS, "ledger_dir": str(tmp_path), "pacer": fetchgate.Pacer(sleep=lambda s: None)}


def test_an_ask_goes_through_the_gate_with_our_key_and_a_block_is_a_failed_read(monkeypatch, tmp_path):
    seen = []

    def fake(url, timeout):
        seen.append(url)
        return 429, b"", url
    got, ref = capture.fetch_entity(N1, None, key="SECRETKEY", fetch=fake, **_gate(monkeypatch, tmp_path))
    assert ref is None and "hard limit 6" in got.blocked and seen == [capture.entity_url(N1)]
    got, ref = capture.fetch_entity(N1, None, key="SECRETKEY", fetch=lambda u, t: (200, b"<html>captcha</html>", u),
                                    **_gate(monkeypatch, tmp_path))
    assert ref is None and got.blocked
    ledger = open(next(tmp_path.iterdir()), encoding="utf-8").read()
    assert "SECRETKEY" not in ledger and "nzbn-register-entities" in ledger


def test_without_a_position_the_gate_refuses(monkeypatch, tmp_path):
    g = _gate(monkeypatch, tmp_path)
    g["positions_dir"] = str(tmp_path)
    with pytest.raises(fetchgate.Refused):
        capture.fetch_entity(N1, None, key="SECRETKEY", fetch=lambda u, t: (200, b"{}", u), **g)
    with pytest.raises(ValueError):
        capture.entity_url("12345")


# --- the outside check ----------------------------------------------------------------

def test_the_check_counts_the_register_s_societies_against_the_lane_s():
    lane_rows = {N1: ("EXAMPLE HOCKEY CLUB INCORPORATED", "registered"), N2: ("OTHER HOCKEY INC", "removed"),
                 "9429000000031": ("HOCKEY ASSOCIATION INCORPORATED", "registered")}
    items = {N1: "1990-01-01", N2: "1991-01-01", "9429000000048": "2026-09-01", "9429000000055": "2000-01-01"}
    f = check.compare("hockey", 4, items, lane_rows, "2026-08-04")
    assert (f["equal"], f["other_status"], f["after_the_file"], f["missing"], f["lane_named"], f["unfound"]) == (1, 1, 1, 1, 2, 1)
    assert len(check.failed({"terms": [f]})) == 3


# --- the filled sample ------------------------------------------------------------------

def _schema():
    return "scratch_gate_societies"


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
        t = {n: q(f"SELECT * FROM {schema}.societies_{n} ORDER BY key") for n in
             ("societies", "society_states", "officers", "asks")}
        yield {"schema": schema, "conn": conn, **t, "aside": q(f"SELECT * FROM {schema}.societies_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.societies_officer_addresses")}


def test_every_listed_society_is_held_once(filled):
    from registers.societies import sample as S
    listed = S.keys_of(sample.read_list(os.path.join(LANE, "sample.list")))
    assert {s["nzbn"] for s in filled["societies"]} == listed


def test_each_case_reads_as_its_comment_says(filled):
    party = {s["nzbn"] for s in filled["societies"] if s["party_society"]}
    assert party == {"9429042857310", "9429043384211", "9429047844483", "9429053326102", "9429053605498"}
    assert any(s["society_key"] == "societies/9429000000000" for s in filled["society_states"])
    assert any(o["key"].endswith("/2") for o in filled["officers"] if o["nzbn"] == "9429042577980")
    assert any(o["started_on"] is None for o in filled["officers"] if o["nzbn"] == "9429047444997")
    assert not [o for o in filled["officers"] if o["nzbn"] in ("9429042586500", "9429000032179")]
    assert any("kept from an earlier ask" in a["reason"] for a in filled["aside"])
    answered = [o for o in filled["officers"] if o["nzbn"] == "9429042857310"]
    assert answered and all(o["profile"] == read.ANSWER_PROFILE for o in answered)
    assert len([a for a in filled["asks"] if a["nzbn"] == "9429042857310"]) == 2


def test_no_end_date_is_a_load_day(filled):
    loaded = {o["loaded_at"].date() for o in filled["officers"]}
    assert not [o for o in filled["officers"] if o["ended_on"] in loaded]
    assert all(o["role_status"] == "Inactive" for o in filled["officers"] if o["ended_on"])


def test_no_address_is_held_or_published(filled):
    assert filled["private"] == []                  # neither the old table nor the five answers carry one
    for t in ("societies", "officers"):
        assert not set(filled[t][0]) & {"address", "line_1", "postcode", "residential_address", "role_address"}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("societies", "society_states", "officers", "asks"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version",
                                     "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            assert rowcontract.validate(row, today) == [], (t, r["key"])


def test_the_published_views_build_and_carry_no_private_column(filled):
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(load.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.societies_pub_"))
    views = ("societies", "society_states", "society_officers")
    counts = {v: conn.execute(f"SELECT count(*) FROM {schema}.societies_pub_{v}").fetchone()[0] for v in views}
    cols = {v: [d[0] for d in conn.execute(f"SELECT * FROM {schema}.societies_pub_{v} LIMIT 0").description]
            for v in views}
    conn.rollback()
    assert counts["societies"] == len(filled["societies"]) and counts["society_officers"] == len(filled["officers"])
    assert not any(c in ("old_id", "private_ref", "unique_identifier") for cs in cols.values() for c in cs)
    assert not set(cols["society_officers"]) & set(rowcontract.FORBIDDEN_COLUMNS)


def test_the_outside_check_measures_the_lane_s_own_table(filled):
    f = check.figures(filled["conn"], load.table(filled["schema"], "societies", True))
    assert f["cut"] and [t["term"] for t in f["terms"]] == list(check.SEARCHES)


def test_off_peak_is_one_to_six_and_never_the_wednesday_window():
    nz = dt.timezone(dt.timedelta(hours=13))
    assert capture.off_peak(dt.datetime(2026, 10, 20, 2, 0, tzinfo=nz))
    assert not capture.off_peak(dt.datetime(2026, 10, 20, 7, 0, tzinfo=nz))
    assert not capture.off_peak(dt.datetime(2026, 10, 21, 22, 0, tzinfo=nz))      # a Wednesday


class _Conn:
    """Answers the night's three reads; nothing else."""
    def __init__(self, socs):
        self.socs = socs

    def execute(self, sql, params=()):
        if "FROM societies.societies" in sql:
            return iter(self.socs)
        return iter(())

    def commit(self):
        pass


def test_a_night_asks_party_first_stops_at_a_block_and_its_failed_ask_moves_the_clock(monkeypatch, tmp_path):
    g = _gate(monkeypatch, tmp_path)
    monkeypatch.setattr(capture, "POSITIONS", g["positions_dir"])
    monkeypatch.setattr(capture, "LANE_FLOOR_S", 0.0)
    monkeypatch.setattr("support.jobrun.RUNS", str(tmp_path / "runs.jsonl"))
    monkeypatch.setattr(fetchgate, "LEDGER_DIR", str(tmp_path / "gate"))
    socs = [(N1, "A CLUB INCORPORATED", "registered"), (N2, "THE EXAMPLE PARTY OF NEW ZEALAND INCORPORATED", "registered")]
    seen = []

    def fake(url, timeout):
        seen.append(url)
        return 503, b"", url
    ledger = str(tmp_path / "asks.jsonl")
    out = capture.night(_Conn(socs), anytime=True, key="SECRETKEY", fetch=fake, pacer=g["pacer"], ledger=ledger,
                        log=lambda *a: None)
    assert seen == [capture.entity_url(N2)] and not out["ok"] and out["failed"] == 1
    assert capture.clock(_Conn(socs), ledger)[N2]
    assert "SECRETKEY" not in open(ledger).read() + open(tmp_path / "runs.jsonl").read()
