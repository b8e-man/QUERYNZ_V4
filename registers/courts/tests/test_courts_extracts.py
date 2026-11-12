"""The courts lane and its profiles aligned (Arthur, 3 November 2026): what the code produces is what the profiles list,
every column is fed by a field, and every document read is recorded in docs.extractions. Invented values only."""
import dataclasses

import pytest

import support.profiles as pr
from support.profiles import align
from registers.courts import caption, check, extracts, identifiers, model_read
from registers.courts import load as L
from registers.courts import read as R

#: the reading version each profile's stored readings are keyed by, before the extract lists were added (3 November)
READING_VERSIONS = {"courts-case-page": 2, "courts-case-synopsis": 2, "courts-counsel-submission": 2,
                    "courts-era-determination": 1, "courts-hearing-transcript": 2, "courts-hrrt-decision": 1,
                    "courts-judgment": 2, "courts-maori-court-judgment": 1, "courts-media-release": 2,
                    "courts-nzca-judgment": 3, "courts-nzdc-judgment": 1, "courts-nzhc-civil-judgment": 3,
                    "courts-nzhc-criminal-judgment": 3, "courts-nzsc-judgment": 3, "courts-scanned-document": 1,
                    "courts-tribunal-decision": 1, "courts-waitangi-record-document": 1, "courts-waitangi-report": 1, "courts-era-early-determination": 1}
#: the fields iteration 3 moved or added: read.from_mcp
MCP_FIELDS = ("citation", "judgment_date", "date_basis", "citation_basis")


def test_every_courts_profile_lists_what_it_extracts_and_keeps_its_reading_version():
    cur = pr.current()
    assert set(extracts.SLUGS) == set(READING_VERSIONS) == {s for s in cur if s.startswith("courts-")}
    for slug, v in READING_VERSIONS.items():
        prof = cur[slug]
        assert prof["extract"], slug
        assert R.profile_version(slug) == pr.reading_version(slug) == v, f"{slug}: a stored reading would be orphaned"
        items = pr.latest(prof["extract"])
        if slug == R.SCANNED:
            assert prof["iteration"] == 1 and set(items) == {"page_text"}
            continue
        ids = items["identifiers"]
        # iteration 3 (ruling 1, 3 November 2026): the pattern pass as at 2, its NZBN and company number naming judgment-number@1;
        # iteration 4 (ruling 142, 4 November 2026): the same, its email, phone and address naming the links rules that read them
        assert (ids["iteration"], ids["by"], ids["private"]) == (4, "pattern", True)
        assert {ln["key"]: ln["rule"] for ln in ids["links"]}["email"] == "shared-contact@1"
        assert {ln["rule"] for ln in ids["links"] if ln["key"] == "address"} >= {"judgment-address-office@1", "judgment-address-title@1"}
        assert {ln["key"]: ln["rule"] for ln in ids["links"]}["nzbn"] == "judgment-number@1"
        assert {ln["key"]: ln["rule"] for ln in ids["links"]}["company_number"] == "judgment-number@1"
        two = [it for it in prof["extract"] if it["field"] == "identifiers" and it["iteration"] == 2][0]
        three = [it for it in prof["extract"] if it["field"] == "identifiers" and it["iteration"] == 3][0]
        assert {k: v for k, v in three.items() if k not in ("iteration", "links")} == {k: v for k, v in ids.items() if k not in ("iteration", "links")}
        assert {k: v for k, v in two.items() if k not in ("iteration", "links")} == {k: v for k, v in ids.items() if k not in ("iteration", "links")}
        assert ids["kinds"] == list(identifiers.SHAPE_KINDS)
        assert all(c.startswith(L.PRIVATE + ".identifiers.") for c in ids["lands"])
        # iteration 3 (3 November 2026, the judgments only): the MCP's date and citation where the document gives none
        mcp = set(MCP_FIELDS) if slug in R.JUDGMENT_SLUGS else set()
        # the next iteration of the citation and the case numbers (ruling 4, 3 November 2026): case-documents@1
        case = {f for f, key in (("citation", "citation"), ("case_numbers", "case_number"))
                if f in items and any(ln["key"] == key for ln in items[f]["links"])}
        for f in case:
            key = "citation" if f == "citation" else "case_number"
            base = 3 if f in mcp else 1
            assert items[f]["iteration"] == base + 1, (slug, f)
            assert {ln["key"]: ln["rule"] for ln in items[f]["links"]}[key] == "case-documents@1", (slug, f)
        assert prof["iteration"] == max(it["iteration"] for it in items.values()), slug
        # ruling 142 (Arthur, 4 November 2026: keep everything): the iteration after the last one that came before it
        # asks the text reader for each person's details (private, by model) and moves the fields a suppression reaches
        # from withholding to a flag with the name kept privately
        keep = 5 if slug in R.JUDGMENT_SLUGS else 4
        kept = {"people", "for_party", "suppression", "details"} | ({"parties"} if "parties" in items else set()) | \
            ({"case_name"} if "case_name" in items else set())
        # the details at the iteration after (ruling 142, 4 November 2026): the same ask, its links naming the rules that read them
        assert items["details"]["iteration"] == keep + 1, slug
        assert {ln["key"]: ln["rule"] for ln in items["details"]["links"]}.get("email") == "shared-contact@1", slug
        assert {f for f, it in items.items() if it["iteration"] == keep} - {"identifiers"} == kept - {"details"}, slug
        assert (items["details"]["by"], items["details"]["private"], items["details"]["kinds"]) == \
            ("model", True, list(model_read.DETAIL_KINDS)), slug
        assert all(c.startswith(L.PRIVATE + ".identifiers.") for c in items["details"]["lands"])
        assert "courts_private.withheld_names.suppression_words" in items["suppression"]["lands"], slug
        assert not any(w in it["ask"] for w in (" is withheld", "withheld under", "is published but", "never add")
                       for it in items.values() if it["iteration"] == keep), slug
        assert {f for f, it in items.items() if it["iteration"] == 3} == (mcp - case - kept), slug
        assert all(it["iteration"] == 1 and not it["private"] for f, it in items.items() if f not in mcp | case | kept | {"identifiers"}), slug
        assert all(items[f]["by"] == "rules" and not items[f]["private"] for f in mcp)
        assert not any(it["iteration"] > keep + 1 for it in prof["extract"]), slug


def test_the_lane_and_its_profiles_are_aligned():
    assert extracts.problems() == []


def _profiles_with(slug, change):
    cur = pr.current()
    prof = dict(cur[slug])
    prof["extract"] = change(list(prof["extract"]))
    return {**cur, slug: prof}


def test_a_profile_field_no_code_produces_is_red():
    extra = {"field": "registry_of_deeds", "iteration": 3, "by": "rules", "ask": "x", "private": False, "kinds": None,
             "lands": ["judgments.registry"], "links": []}
    got = extracts.problems(_profiles_with("courts-nzsc-judgment", lambda ex: ex + [extra]))
    assert got == ["courts-nzsc-judgment: the profile lists registry_of_deeds (iteration 3); no code of the courts lane produces it"]


def test_a_field_the_code_produces_and_the_profile_lacks_is_red():
    got = extracts.problems(_profiles_with("courts-media-release", lambda ex: [i for i in ex if i["field"] != "dated"]))
    assert "courts-media-release: the courts lane produces dated (rules); the profile's extract list lacks it" in got


def test_a_lane_column_no_profile_field_lands_in_is_red():
    lane = align.Lane("courts", {**extracts.TABLES, "judgments": extracts.TABLES["judgments"] + ("bench_size",)},
                      extracts.LANE.produces, extracts.HOUSEKEEPING)
    assert align.problems(lane) == ["judgments.bench_size: a column of the courts lane's tables that no profile's field lands in"]


def test_a_lands_column_the_tables_lack_is_red():
    tables = {**extracts.TABLES, "judgments": tuple(c for c in extracts.TABLES["judgments"] if c != "counsel_roles")}
    got = align.problems(align.Lane("courts", tables, extracts.LANE.produces, extracts.HOUSEKEEPING))
    assert got and all("counsel_roles lands in judgments.counsel_roles, which is not a column" in p for p in got)
    assert len(got) == len(R.JUDGMENT_SLUGS)


def test_the_fields_are_the_code_s_own():
    assert set(caption.FIELDS) == {f.name for f in dataclasses.fields(caption.Judgment)} - set(caption.DIAGNOSTIC)
    assert set(R.sheet_fields()) == set(R.sheet({1: "x"}, R.TRANSCRIPT))
    answer = model_read.parse_answer('{"summary": "s", "people": [{"name": "Ann Example", "kind": "person", "role": "counsel", '
                                     '"role_text": "counsel for the appellant", "for": "Example Holdings Limited"}]}')
    person_keys = {k for f, keys in model_read.FIELDS.items() if f != "summary" for k in keys}
    assert person_keys == set(answer["people"][0]) and "summary" in answer


def test_the_case_page_fields_cover_what_the_grammar_writes():
    """Every column `_case_rows` fills is landed by a case page field (the grammar and the profile cannot drift)."""
    page = {"case_name": "Ann Example v Example Holdings Limited", "citation": "[2099] NZSC 1", "case_numbers": ["SC 1/2099"],
            "court": "Supreme Court", "links": [("Decision", "Judgment", "https://example.invalid/j.pdf")],
            "sections": {"Summary": "s", "Result": "r", "Judges": "j", "Date of Judgment": "1 January 2099",
                         "Date of Hearing": "1 January 2099"}}
    res = R.Result()
    R._case_rows(res, {"url": "https://example.invalid/cases/x", "case_slug": "x"}, "a" * 64, page, R.CASE_PAGE, 2, {}, "now")
    written = {f"cases.{c}" for c in res.cases[0]} | {f"case_links.{c}" for c in res.case_links[0]}
    lands = {c for it in pr.latest(pr.profile(R.CASE_PAGE)["extract"]).values() for c in it["lands"]}
    assert {c for c in written if not extracts.LANE.is_housekeeping(c)} <= lands


def _doc(sha, slug, outcome, model=None, read_from="text"):
    return {"document": sha, "profile": slug, "outcome": outcome, "model": model, "model_reader": "m 2" if model else None,
            "read_from": read_from}


def test_a_document_records_the_fields_it_had_at_their_iterations():
    a, b, c, d = "a" * 64, "b" * 64, "c" * 64, "d" * 64
    rows = extracts.extracted([
        _doc(a, "courts-nzsc-judgment", "read", model="served-model"),
        _doc(a, "courts-nzsc-judgment", "read", model="served-model"),          # a second record of the same file
        _doc(b, "courts-media-release", R.WAIT_TEXT, read_from="mixed"),
        _doc(c, R.SCANNED, R.WAIT_PAGES, read_from="pixels"),
        _doc(d, None, "caught")])
    got = {(s[:1], p, f, n, m) for s, p, f, n, _, m in rows}
    assert len(rows) == len(got)
    a_fields = {f for s, p, f, n, m in got if s == "a"}
    assert a_fields == set(caption.FIELDS) | set(model_read.FIELDS) | {"identifiers"}
    assert ("a", "courts-nzsc-judgment", "identifiers", 4, None) in got and ("a", "courts-nzsc-judgment", "people", 5, "served-model") in got
    assert ("a", "courts-nzsc-judgment", "details", 6, "served-model") in got
    b_fields = {(p, f) for s, p, f, n, m in got if s == "b"}
    assert b_fields == {("courts-media-release", f) for f in R.sheet_fields()} | {("courts-media-release", "identifiers"),
                                                                                   (R.SCANNED, "page_text")}
    assert not any(s in ("c", "d") for s, *_ in got)
    assert extracts.expected("courts-media-release", R.WAIT_TEXT) == set(R.sheet_fields()) | {"identifiers"}
    assert extracts.expected("courts-media-release", "read") == {f for _, f in b_fields if f != "page_text"} | set(model_read.FIELDS)


def test_the_check_fails_a_document_read_without_its_ledger_row(monkeypatch):
    from support.docstore import extraction
    shas = ["e" * 64, "f" * 64]

    class Conn:
        def execute(self, sql, args=()):
            rows = [(s, "courts-media-release", "read", "text") for s in shas]
            return type("R", (), {"fetchall": lambda self: rows})()

    full = {f: 0 for f in extracts.expected("courts-media-release", "read")}
    monkeypatch.setattr(extraction, "behind", lambda conn, slug, docs: dict(full))
    failures = []
    assert check._extractions(Conn(), lambda n: n, failures) == {} and failures == []
    monkeypatch.setattr(extraction, "behind", lambda conn, slug, docs: {**full, "people": 1})
    out = check._extractions(Conn(), lambda n: n, failures)
    assert out == {"courts-media-release (read, 2)": {"people": 1}}
    assert failures == ["courts-media-release: 1 of 2 documents read have no docs.extractions row for people at its current iteration"]


def test_the_check_runs_the_alignment(monkeypatch):
    monkeypatch.setattr(extracts, "problems", lambda profiles=None: ["courts-x: invented"])
    monkeypatch.setattr(align, "live_problems", lambda conn, lane, where, profiles=None: ["courts.judgments has no column y"])
    failures = []
    check._alignment(None, "courts", False, failures)
    assert failures == ["alignment: courts-x: invented", "alignment: courts.judgments has no column y"]
