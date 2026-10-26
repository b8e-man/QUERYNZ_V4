"""The hansard lane's tests (ruling 96). The reader and the check are tested
on small exports shaped like the old estate's (every member and text
invented); the filled sample is tested against the row contract, the
sitting rows' own counts, the old derived speeches and the published views.
No model is called."""
import datetime as dt
import hashlib
import json
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.hansard import capture, check, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "hansard")
SHA = "0" * 64
URL = "https://hansard.parliament.nz/hansard-transcript/2025-01-02"


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_the_export_is_pinned_and_the_sample_names_it():
    assert len(capture.EXPORT_SHA) == 64 and capture.EXPORTED_AT.startswith("2026-10-26")
    assert capture.EXPORT_SHA in sample.read_list(os.path.join(LANE, "sample.list"))


# --- the export's bytes and the reading ---------------------------------------------

def _section(day, idx, speakers, text="Words.", **kw):
    return {"id": f"old-{day}-{idx}", "sitting_date": day, "section_index": idx, "parliament": 54, "volume": 780,
            "proceeding": "Bills", "subject": "Example Bill", "bill_title": None, "bill_id": None, "body_text": text,
            "char_count": len(text), "speakers": speakers, "speech_count": len(speakers), "url": URL,
            "source": "hansard.parliament.nz", "status": "captured", "progress": "Corrected",
            "body_hash": hashlib.sha1(text.encode()).hexdigest(), "fetched_at": "2026-09-01T00:00:00+12:00", **kw}


ANN = {"name": "Able, Hon Ann", "role": None, "label": "Hon ANN ABLE", "member_id": "m-ann"}
BOB = {"name": "Baker, Bob", "role": None, "label": "BOB BAKER", "member_id": "m-bob"}
CHAIR = {"name": None, "role": "Speaker", "label": "SPEAKER", "member_id": None}


def _export(sections=None, sittings=None, speeches=None):
    members = [{"member_id": "m-ann", "display_name": "Able, Hon Ann", "sort_name": "able ann", "parliaments": [54]},
               {"member_id": "m-bob", "display_name": "Baker, Bob", "sort_name": "baker bob", "parliaments": [54]}]
    sections = sections if sections is not None else [_section("2025-01-02", 1, [ANN, CHAIR, BOB, ANN]),
                                                      _section("2025-01-02", 2, [], text="")]
    sittings = sittings if sittings is not None else [
        {"sitting_date": "2025-01-02", "parliament": "54", "volume": "780", "progress": "Corrected", "sections": 2,
         "speeches": 3, "speakers": 2, "resolved": 2, "unresolved": 0, "unattributed": 1, "derived_at": None}]
    speeches = speeches if speeches is not None else [
        {"id": 1, "sitting_date": "2025-01-02", "section_index": 1, "member_id": "m-ann", "speaker_label": "Hon ANN ABLE",
         "speaker_name": "Able, Hon Ann", "in_roster": True, "speech_count": 2, "proceeding": "Bills", "subject": "x",
         "bill_id": None, "bill_title": None, "progress": "Corrected", "url": URL, "derived_at": None, "retired_at": None},
        {"id": 2, "sitting_date": "2025-01-02", "section_index": 1, "member_id": "m-bob", "speaker_label": "BOB BAKER",
         "speaker_name": "Baker, Bob", "in_roster": True, "speech_count": 1, "proceeding": "Bills", "subject": "x",
         "bill_id": None, "bill_title": None, "progress": "Corrected", "url": URL, "derived_at": None, "retired_at": None}]
    return capture.lines_of(members, sections, sittings, speeches)


def test_the_export_is_the_same_bytes_for_the_same_rows_in_any_order():
    a = _export()
    s = [_section("2025-01-02", 2, [], text=""), _section("2025-01-02", 1, [ANN, CHAIR, BOB, ANN])]
    assert _export(sections=s) == a
    kinds = [json.loads(l)["kind"] for l in a.decode().splitlines()]
    assert kinds == ["member", "member", "section", "section", "sitting", "speech", "speech"]


def test_one_turn_per_speaker_list_entry_in_printed_order_and_a_role_is_not_a_member():
    r = read.read(_export(), SHA)
    assert read.balanced(r) and r.set_aside == []
    assert [(t["key"], t["member_id"], t["label"], t["role"]) for t in r.turns] == [
        ("2025-01-02/1/1", "m-ann", "Hon ANN ABLE", None), ("2025-01-02/1/2", None, "SPEAKER", "Speaker"),
        ("2025-01-02/1/3", "m-bob", "BOB BAKER", None), ("2025-01-02/1/4", "m-ann", "Hon ANN ABLE", None)]
    assert [t["in_roster"] for t in r.turns] == [True, False, True, True]
    s = r.sittings[0]
    assert (s["sections"], s["turns"], s["attributed"], s["unattributed"], s["speakers"]) == (2, 4, 3, 1, 2)
    assert (s["old_sections"], s["old_speeches"], s["old_unattributed"], s["old_speakers"]) == (2, 3, 1, 2)
    assert s["url"] == URL and r.turns[0]["place"] == "sitting 2025-01-02 section 1 turn 1"
    assert {x["source_note"] for x in r.sections + r.turns + r.sittings + r.members} == {capture.EXPORT_NOTE}


def test_a_text_that_does_not_hash_to_its_sha1_is_set_aside_and_the_reading_still_balances():
    bad = _section("2025-01-02", 1, [ANN])
    bad["body_text"] = "Altered."
    r = read.read(_export(sections=[bad, _section("2025-01-02", 2, [])]), SHA)
    assert [k for k, _, _ in r.set_aside] == ["2025-01-02/1"] and read.balanced(r)
    assert [s["key"] for s in r.sections] == ["2025-01-02/2"]


def test_only_reads_the_named_days_and_every_member():
    other = _section("2025-01-03", 1, [BOB])
    r = read.read(_export(sections=[_section("2025-01-02", 1, [ANN]), other]), SHA, only={"2025-01-03"})
    assert [s["key"] for s in r.sections] == ["2025-01-03/1"] and len(r.members) == 2
    assert r.sittings == [] and ("2025-01-03", "read", "sections held for a day the old sittings table has no row for") \
        in r.set_aside


# --- the check -------------------------------------------------------------------

MEMBERS = ["ABLE, Ann Mary", "BAKER, Robert", "CARTER, Cy", "CARTER, Cyril", "DOE, Dee"]


def test_a_speaker_matches_a_member_by_name_with_honorifics_off_and_never_by_surname_alone():
    assert check.match("Able, Hon Ann", MEMBERS) == "first given"
    assert check.match("Able, Rt Hon Ann Mary", MEMBERS) == "full"
    assert check.match("Baker, Bob", MEMBERS) == "none"            # a nickname does not fold
    assert check.match("Baker, Dr Rob", MEMBERS) == "given prefix"
    assert check.match("Carter, Hon Cy", MEMBERS) == "full"
    assert check.match("Carter, C", MEMBERS) == "ambiguous"
    assert check.match("Evans, Eve", MEMBERS) == "none"


def _f(**kw):
    f = {"sittings": [("2025-01-02", [2, 3, 1, 2], [2, 3, 1, 2])], "speeches": [], "bad_hash": [], "set_aside": [],
         "members": check.members_share({"m-ann": ("Able, Hon Ann", 97), "m-bob": ("Baker, Dr Rob", 3)}, MEMBERS)}
    f.update(kw)
    return f


def test_the_check_passes_when_every_figure_agrees():
    assert check.failed(_f()) == []


def test_the_check_fails_on_a_sitting_that_differs_or_has_no_row():
    assert any("2025-01-02" in p for p in check.failed(_f(sittings=[("2025-01-02", [2, 3, 1, 2], [2, 4, 1, 2])])))
    assert any("no sitting row" in p for p in check.failed(_f(sittings=[("2025-01-02", None, None)])))


def test_the_check_fails_on_a_speech_count_a_bad_hash_or_a_catch_log_line():
    assert check.failed(_f(speeches=[("2025-01-02/1/m-ann", 2, 3)]))
    assert check.failed(_f(bad_hash=["2025-01-02/1"]))
    assert check.failed(_f(set_aside=[("line 3", "read", "not a JSON object")]))


def test_the_check_fails_below_either_members_floor_and_without_pub_members():
    few = check.members_share({"m-ann": ("Able, Hon Ann", 50), "m-x": ("Evans, Eve", 1)}, MEMBERS)
    assert any("members matched" in p for p in check.failed(_f(members=few)))
    turns = check.members_share({f"m{i}": ("Able, Ann", 1) for i in range(19)} | {"m-x": ("Evans, Eve", 10)}, MEMBERS)
    assert turns["members_matched"] / turns["members"] >= check.MEMBER_FLOOR
    assert any("member turns" in p for p in check.failed(_f(members=turns)))
    assert any("pub.members" in p for p in check.failed(_f(members=None)))


# --- the filled sample ---------------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_hansard"


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
        yield {"schema": schema, "conn": conn,
               "sittings": q(f"SELECT * FROM {schema}.hansard_sittings ORDER BY key"),
               "sections": q(f"SELECT key, sitting_on, chars, turns, url, old_status, progress, document, page, place, "
                             f"reader, profile, profile_version, read_from, loaded_at FROM {schema}.hansard_sections"),
               "turns": q(f"SELECT * FROM {schema}.hansard_turns"),
               "members": q(f"SELECT * FROM {schema}.hansard_members"),
               "old": q(f"SELECT * FROM {schema}.hansard_old_speeches"),
               "aside": q(f"SELECT * FROM {schema}.hansard_set_aside")}


def test_every_listed_day_is_held_and_nothing_is_set_aside(filled):
    from registers.hansard import sample as S
    listed = S.days_of(sample.read_list(os.path.join(LANE, "sample.list")))
    assert {s["key"] for s in filled["sittings"]} == listed
    assert filled["aside"] == [] and len(filled["members"]) == 394


def test_each_case_reads_as_its_comment_says(filled):
    by = {s["key"]: s for s in filled["sittings"]}
    assert by["2024-11-20"]["progress"] == "Corrected" and by["2026-09-23"]["progress"] == "Draft"
    empty = [s for s in filled["sections"] if str(s["sitting_on"]) == "2026-06-30" and s["chars"] == 0]
    assert len(empty) == 12 and all(s["turns"] == 0 for s in empty)
    assert sum(1 for o in filled["old"] if str(o["sitting_on"]) == "2026-04-01" and o["retired_at"]) == 72
    assert {s["old_status"] for s in filled["sections"] if str(s["sitting_on"]) == "2026-02-11"} >= {"failed"}
    assert by["2025-10-16"]["sections"] == 4 and by["2025-10-16"]["turns"] == 0
    assert all(s["url"].endswith("/hansard-transcript/" + str(s["sitting_on"])) for s in filled["sections"])


def test_every_sitting_and_speech_agrees_with_the_old_estate_s_own_figures(filled):
    f = check.figures(filled["conn"], filled["schema"], shared=True)
    assert f["sittings"] and all(o == p for _, o, p in f["sittings"])
    assert f["speeches"] == [] and f["bad_hash"] == [] and f["set_aside"] == []
    assert sum(s["turns"] for s in filled["sittings"]) == len(filled["turns"])


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("sittings", "sections", "turns", "members"):
        for r in filled[t]:
            row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
            row["loaded_at"] = r["loaded_at"].isoformat()
            row["filed"] = {k: (v.isoformat() if v else None) for k, v in r.items() if k.endswith("_on")}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
            assert row["document"] == capture.EXPORT_SHA


def test_the_published_views_build_on_the_lane_s_tables_and_the_index_join_is_empty(filled):
    from registers.hansard import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.hansard_pub_"))
    n = conn.execute(f"SELECT count(*), count(member_id) FROM {schema}.hansard_pub_hansard_speeches").fetchone()
    s = conn.execute(f"SELECT count(*), count(index_lastmod) FROM {schema}.hansard_pub_hansard_sittings").fetchone()
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.hansard_pub_hansard_sections LIMIT 0").description]
    conn.rollback()
    assert n == (len(filled["turns"]), sum(1 for t in filled["turns"] if t["member_id"]))
    assert s == (len(filled["sittings"]), 0)
    assert "text" in cols and "old_id" not in cols and "old_status" not in cols
