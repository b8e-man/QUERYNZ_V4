"""The lane's reading on hand-made records in the interface's shape (every
name invented; tests/fixture.py), then built into a scratch schema of the
sample database with the views, held to check.py's reading checks, rebuilt
to show the keys do not move. A mutant check breaks the suppression rule
on purpose, seven ways, and requires these properties to catch every break.
No model is called and nothing is fetched."""
import json
import os
import re
import sys

import pytest

from support import db, lane, rowcontract
from registers.openlaw import check, load, read
from registers.openlaw.tests import fixture as F

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA, SHA2 = "a" * 64, "b" * 64
PROF = read.profile()


def _read(rec, sha=SHA, i=0, mod=read):
    rows, why = mod.read_case(rec, sha, i, PROF)
    assert rows is not None, why
    return rows


# ── the profile and recognition ──────────────────────────────────────────────

def test_the_reading_runs_from_its_profile_at_the_version_it_stamps():
    assert PROF["slug"] == read.PROFILE and int(PROF["version"]) == read.PROFILE_VERSION
    assert PROF["recognise"]["max_records"] == read.MAX_RECORDS
    rows = _read(F.clean())
    assert rows["case"]["profile"] == read.PROFILE and rows["case"]["profile_version"] == read.PROFILE_VERSION


def test_a_page_is_recognised_by_its_shape_and_an_answer_with_errors_is_not_a_page():
    assert read.recognise(F.page(F.clean()))[0] is not None
    assert read.recognise(b'{"errors": [{"message": "x"}], "data": null}') == (None, "the interface answered with errors")
    assert read.recognise(b"<html>")[1] == "not JSON"
    assert read.recognise(b'{"data": {"courts": []}}')[1] == "no data.cases list"
    assert "more than the profile's page" in read.recognise(F.page(*[F.clean()] * 11))[1]


# ── one case ─────────────────────────────────────────────────────────────────

def test_a_case_row_carries_the_neutral_citation_court_registry_number_date_id_and_pdf():
    c = _read(F.clean())["case"]
    assert (c["key"], c["citation"], c["court"], c["court_name"], c["registry"], c["filing_number"], c["decided_on"]) == \
        ("hc_test_2024NZHC1001.pdf", "[2024] NZHC 1001", "NZHC", "High Court", "AUCKLAND", "CIV-2023-404-000123", "2024-05-02")
    assert c["pdf_url"].endswith("hc_test_2024NZHC1001.pdf") and c["suppressed"] is False and c["suppression_marks"] == []


def test_the_neutral_citation_is_the_one_of_its_shape_whatever_its_place():
    c = _read(F.criminal())["case"]
    assert c["citation"] == "[2024] NZHC 4004" and c["citations"] == ["CRI-2023-041-000999", "[2024] NZHC 4004"]
    assert read.neutral([{"citation": "[2024]  NZSC  12"}])[0] == "[2024] NZSC 12"
    assert read.neutral([{"citation": "(2024) 1 NZLR 5"}])[0] is None


def test_the_registry_comes_from_the_interface_else_the_caption():
    assert _read(F.anonymised())["case"]["registry"] is None
    assert _read(F.criminal())["case"]["registry"] == "NAPIER"


def test_the_title_goes_to_the_private_twin_not_the_case_row():
    rows = _read(F.clean())
    assert "title" not in rows["case"] and rows["title"] == {"key": F.clean()["id"], "title": F.clean()["caseName"]}


# ── parties ──────────────────────────────────────────────────────────────────

def test_one_party_row_per_name_and_role_from_the_interface_names_apart():
    rows = _read(F.record(parties=(("APPELLANT", ["IOTA LIMITED", "KAPPA LIMITED"]), ("RESPONDENT", ["LAMBDA LIMITED"]))))
    assert [(p["role"], p["position"]) for p in rows["parties"]] == [("APPELLANT", 1), ("APPELLANT", 2), ("RESPONDENT", 3)]
    assert [n["name"] for n in rows["names"]] == ["IOTA LIMITED", "KAPPA LIMITED", "LAMBDA LIMITED"]
    assert all("name" not in p for p in rows["parties"])
    assert {p["from_source"] for p in rows["parties"]} == {"interface"}


def test_with_no_party_table_the_caption_names_them_and_the_criminal_caption_too():
    rows = _read(F.caption_only())
    assert rows["case"]["parties_from"] == "caption"
    assert [(n["name"], p["role"]) for p, n in zip(rows["parties"], rows["names"])] == [
        ("GAMMA TRUSTEE LIMITED", "First Appellant"), ("DELTA EXAMPLE", "Second Appellant"), ("EPSILON COUNCIL", "Respondent")]
    rows = _read(F.criminal())
    assert [(n["name"], p["role"], p["crown"]) for p, n in zip(rows["parties"], rows["names"])] == [
        ("THE KING", "Prosecutor", True), ("ZETA EXAMPLE", "Defendant", False)]


def test_a_record_naming_no_party_has_none_and_says_so():
    c = _read(F.record(parties=(), text="[1] Invented, no caption."))["case"]
    assert c["parties_from"] == "none"


# ── suppression (hard limit 16) ──────────────────────────────────────────────

def suppression_properties(mod) -> list:
    """What the suppression rule must hold, as problems; [] when it holds.
    Run on the reading and on every mutant of it."""
    out = []
    try:
        s = mod.read_case(F.suppressed(), SHA, 0, PROF)[0]
        a = mod.read_case(F.anonymised(), SHA, 0, PROF)[0]
        c = mod.read_case(F.clean(), SHA, 0, PROF)[0]
        t = mod.read_case(F.record("x_test_1", name="Re an applicant [name suppressed]"), SHA, 0, PROF)[0]
        k = mod.read_case(F.record("x_test_2", text="[1] Invented.\n" * 3000 + "[90] ORDER PROHIBITING PUBLICATION OF THE "
                                 "NAME OF THE APPLICANT."), SHA, 0, PROF)[0]
    except Exception as exc:  # noqa: BLE001 — a mutant that crashes is caught
        return [f"crashed: {type(exc).__name__}"]
    if not s["case"]["suppressed"]:
        out.append("a text marker did not mark the case")
    if [p["withheld"] for p in s["parties"]] != [False, True]:
        out.append("in a suppressed case the Crown is shown and every other party withheld")
    if not a["case"]["suppressed"] or not all(p["withheld"] for p in a["parties"]):
        out.append("an anonymised party suppresses the case and withholds every non-Crown name")
    if [n["name"] for n in a["names"]][0] != "W" or not a["parties"][0]["anonymised"]:
        out.append("an anonymised party is kept as the court wrote it and flagged")
    if c["case"]["suppressed"] or any(p["withheld"] for p in c["parties"]):
        out.append("a case with no marker withholds nothing")
    if not t["case"]["suppressed"]:
        out.append("a title's marker marks the case")
    if not k["case"]["suppressed"] or not all(p["withheld"] for p in k["parties"]):
        out.append("an order at the end of the text marks the case")
    return out


def test_the_suppression_rule_holds():
    assert suppression_properties(read) == []


def test_suppression_markers_are_named_never_quoted():
    c = _read(F.suppressed())["case"]
    assert set(c["suppression_marks"]) >= {"order-prohibiting-publication"}
    assert all(m in dict(read.MARKS) or m in ("anonymised-party", "title-suppressed") for m in c["suppression_marks"])


MUTANTS = (
    ("withheld never set", "\"withheld\": suppressed and not crown", "\"withheld\": False"),
    ("the Crown withheld too", "\"withheld\": suppressed and not crown", "\"withheld\": suppressed"),
    ("no text markers", "out = [n for n, rx in _MARKS if case_text and rx.search(case_text)]", "out = []"),
    ("text markers on the head only", "if case_text and rx.search(case_text)]", "if case_text and rx.search(case_text[:300])]"),
    ("anonymised party ignored", "found.append(\"anonymised-party\")", "pass"),
    ("no title markers", "out += [n for n, rx in TITLE_MARKS if title and rx.search(title)]", "pass"),
    ("anonymisation never seen", "return not is_crown(n) and any(rx.search(n) for rx in ANON)", "return False"),
)


@pytest.mark.parametrize("label,old,new", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_a_mutant_of_the_suppression_rule_is_caught(label, old, new):
    src = open(read.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant {label!r} no longer applies: its text is not in read.py once"
    mod = type(sys)("openlaw_read_mutant")
    mod.__file__ = read.__file__
    exec(compile(src.replace(old, new), "read.py (mutant)", "exec"), mod.__dict__)
    assert suppression_properties(mod), f"the mutant {label!r} passed every property"


# ── citations, statutes, the catch log ───────────────────────────────────────

def test_the_citation_graph_and_the_statute_links_are_rows_and_their_faults_set_aside():
    rows = _read(F.caption_only())
    assert [(c["citing_key"], c["cited_key"], c["citation_count"]) for c in rows["citations"]] == [
        ("ca_test_2024NZCA55.pdf", "hc_test_2024NZHC1001.pdf", 1)]
    assert [(s["legislation_id"], s["section"], s["legislation_title"]) for s in rows["statutes"]] == [
        ("rma-1991", "s 104", "Companies Act 1993")]
    assert sorted(a["reason"] for a in rows["asides"]) == [
        "a citation with no cited case", "the same cited case twice in one record",
        "the same statute and section twice in one record"]


def test_a_record_the_profile_does_not_describe_is_set_aside_with_its_reason():
    assert read.read_case("x", SHA, 0, PROF) == (None, "not an object")
    assert read.read_case({**F.clean(), "id": None}, SHA, 0, PROF) == (None, "no id")
    r = F.clean()
    del r["experimentalPartyAndRepresentatives"]
    assert read.read_case(r, SHA, 0, PROF)[1].startswith("the record lacks experimentalPartyAndRepresentatives")


def test_pages_are_read_newest_landed_first_and_a_case_read_again_is_superseded():
    newer = F.record(filing="CIV-2023-404-000124")
    pages = {SHA: F.page(F.clean(), F.suppressed()), SHA2: F.page(newer)}
    got = list(read.read_pages([SHA, SHA2], pages.__getitem__, PROF))
    kinds = [(k, s[:1]) for k, s, _ in got]
    assert kinds == [("page", "b"), ("case", "b"), ("page", "a"), ("superseded", "a"), ("case", "a")]
    assert got[1][2]["case"]["filing_number"] == "CIV-2023-404-000124"


def test_an_unrecognised_page_is_one_catch_log_line():
    got = list(read.read_pages([SHA], {SHA: b'{"errors": [{}]}'}.__getitem__, PROF))
    assert got[1][0] == "aside" and got[1][2]["stage"] == "recognise"


def test_every_row_meets_the_row_contract():
    for rec in (F.clean(), F.suppressed(), F.anonymised(), F.caption_only(), F.criminal()):
        rows = _read(rec)
        for r in [rows["case"]] + rows["parties"] + rows["citations"] + rows["statutes"]:
            assert rowcontract.validate({**r, "loaded_at": "2026-10-21T00:00:00+13:00",
                                         "filed": {"decided_on": rows["case"]["decided_on"]}}) == [], r["key"]


def test_no_row_and_no_view_carries_an_address_or_counsel():
    from registers.openlaw import capture
    assert "appearance" not in capture.CASE_FIELDS and "address" not in capture.CASE_FIELDS.lower()
    sql = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read().split("CREATE OR REPLACE VIEW")
    for v in sql[1:]:
        cols = v.split(" FROM ")[0]
        assert not re.search(r"\baddress|\bappearance|case_?text", cols, re.I)


def test_the_lane_folder_has_the_shape():
    assert lane.check_folder(LANE) == []


# ── built into a scratch schema, with the views ──────────────────────────────

SCHEMA = "scratch_openlaw_lane"
PAGES = {SHA: F.page(F.clean(), F.suppressed(), F.anonymised()), SHA2: F.page(F.caption_only(), F.criminal(), {"id": None})}


def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _digest(conn):
    out = {}
    for t in load.TABLES + load.PRIVATE_TABLES:
        order = "key" if "key" in load.COLUMNS[t] else ", ".join(load.COLUMNS[t])
        out[t] = conn.execute(f"SELECT count(*), md5(coalesce(string_agg(md5((to_jsonb(x) - 'loaded_at')::text), '' "
                              f"ORDER BY {order}), '')) FROM {load.table(SCHEMA, t)} x").fetchone()
    return out


@pytest.fixture(scope="module")
def built():
    _db_or_skip()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        counts = load.build(conn, SCHEMA, [SHA, SHA2], PAGES.__getitem__)
        conn.execute(load.sql("publish.sql", SCHEMA, pub=SCHEMA))
        conn.commit()
        yield conn, counts


def test_the_build_reconciles_and_holds_to_the_reading_checks(built):
    conn, counts = built
    assert (counts["cases"], counts["set_aside"], counts["suppressed"]) == (5, 4, 2)
    r = check.reading(conn, SCHEMA, views=SCHEMA)
    assert r["ok"], r["problems"]
    assert r["figures"]["records"] == 6 and r["figures"]["typed"] == 5 and r["figures"]["parties_withheld"] == 3
    assert r["figures"]["parties_per_case"] == {2: 4, 3: 1}


def test_the_views_withhold_a_suppressed_name_and_title_and_keep_the_rows(built):
    conn, _ = built
    rows = conn.execute(f"SELECT case_key, role, name, name_withheld FROM {SCHEMA}.court_case_parties ORDER BY key").fetchall()
    sup = [r for r in rows if r[0] in ("hc_test_2024NZHC2002.pdf", "ca_test_2024NZCA3003.pdf")]
    assert len(sup) == 4 and [r[2] for r in sup if r[3]] == [None, None, None]
    assert ("hc_test_2024NZHC2002.pdf", "RESPONDENT", "R", False) in sup
    assert ("hc_test_2024NZHC1001.pdf", "PLAINTIFF", "ALPHA WIDGETS LIMITED", False) in rows
    titles = dict(conn.execute(f"SELECT key, title FROM {SCHEMA}.court_cases").fetchall())
    assert titles["hc_test_2024NZHC2002.pdf"] is None and titles["ca_test_2024NZCA3003.pdf"] is None
    assert titles["hc_test_2024NZHC1001.pdf"] == F.clean()["caseName"]


def test_a_view_that_shows_a_withheld_name_fails_the_check(built):
    """The publish.sql mutant: the CASE dropped; check.reading must go red."""
    conn, _ = built
    bad = load.sql("publish.sql", SCHEMA, pub=SCHEMA).replace("CASE WHEN p.withheld THEN NULL ELSE n.name END", "n.name")
    with conn.transaction():
        conn.execute(bad)
        r = check.reading(conn, SCHEMA, views=SCHEMA)
        assert not r["ok"] and any("withheld name" in p for p in r["problems"])
        conn.execute(load.sql("publish.sql", SCHEMA, pub=SCHEMA))


def test_a_rebuild_gives_the_same_rows_under_the_same_keys(built):
    conn, _ = built
    first = _digest(conn)
    load.build(conn, SCHEMA, [SHA, SHA2], PAGES.__getitem__)
    conn.execute(load.sql("publish.sql", SCHEMA, pub=SCHEMA))
    conn.commit()
    assert _digest(conn) == first


def test_the_session_reader_cannot_see_a_name(built):
    conn, _ = built
    for t in ("parties", "cases"):
        cols = {r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                           "AND table_name = %s", (SCHEMA, t))}
        assert cols and not cols & {"name", "title"}
