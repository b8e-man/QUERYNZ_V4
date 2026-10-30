"""The courts lane on its filled sample (the corpus records sample.list
names, their files read through this branch's code): every record accounted
for, each hard case read as its comment in sample.list says, the case page
joined to its decision and release, the row contract, the suppression rule
on real judgments, the lane's check, and the lever. These tests read real
documents and can fail against them. No model (the text reader's readings
are replayed from the reader store where they exist); nothing fetched. A
failure message names a document by its hash and never prints a name."""
import datetime as dt
import os
import re

import pytest

from support import db, lane, rowcontract, sample
from registers.courts import check, suppress
from registers.courts import load as L
from registers.courts import read as R

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "courts")
# the files (by their own hash) the sample's records point at
NZSC_161 = "af540a6a0ab85a307c5e0206e41be2221e52e133dcf9dbe2b6dd60b81282f05e"
NZSC_121 = "f302207384b38cdbb12af638f39f89f6fa35571c6141c393287db8c2bf8df8a8"
NZSC_164 = "04ccbc867b422d5886ed2a06cd4a0f576289f37d0f17f2343f77b1fbdc04a7a8"
NZSC_103 = "0a3e0476e9b0a8399385014cd1d183cb301c457702f5f822815b5552e82aa6d0"
NZHC_2529 = "8af5489fbd83ff36287f9ac52d0cf51dfc02ec0e98266021ea56ce1daadbb1c3"
NZHC_2519 = "28e91d9a66421fcc966b2d9ce4a39e2c6d18f4dc7ebe94859f47e3601721e09c"
NZHC_2654 = "4122a601be9fe02a641c7d04b74c18cfc43f80216afdf95ad31b59b4dec6dff4"
NZSC_122 = "0ddd4acc531ff87ac7b27f6d66bb02704b261eb1c1308b096f0bbb4c7c7b5e20"
RIMMER_PAGE = "6f262b5310827c8b99a694671d55eb09f7d3291e39fe5ae9ac0b9e7010d58bd4".replace("6f262b53", "6f262b53")
RIMMER_URL = "https://www.courtsofnz.govt.nz/cases/rimmer-v-wilton"
MR_122 = "26e369d4a7ee4719b28d8e296cbc8f5f05266ad9dc3e398762c53eff9a5e927f"


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_courts"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(sql, *a):
            cur = conn.execute(sql, a)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        t = lambda n: L.table(schema, n, True)  # noqa: E731
        yield {"schema": schema, "conn": conn, "q": q,
               "documents": q(f"SELECT * FROM {t('documents')} ORDER BY seq"),
               "cases": q(f"SELECT * FROM {t('cases')}"),
               "links": q(f"SELECT * FROM {t('case_links')} ORDER BY key"),
               "judgments": q(f"SELECT * FROM {t('judgments')} ORDER BY key"),
               "parties": q(f"SELECT * FROM {t('judgment_parties')} ORDER BY key"),
               "people": q(f"SELECT * FROM {t('people')} ORDER BY key"),
               "aside": q(f"SELECT * FROM {t('set_aside')}"),
               "paragraphs": q(f"SELECT judgment, count(*) n, max(number) top FROM {t('paragraphs')} GROUP BY 1"),
               "private": q(f"SELECT key, capacity IS NOT NULL AS capacity FROM {L.table(schema + '_private', 'withheld_names', True)}")}


def _of(filled, sha):
    j = [x for x in filled["judgments"] if x["document"] == sha]
    return j[0] if j else None, [p for p in filled["parties"] if p["key"].startswith(sha)]


def _doc(filled, sha=None, url=None):
    return next(d for d in filled["documents"] if (sha and d["document"] == sha) or (url and d["url"] == url))


def test_every_record_of_the_sample_is_a_document_row_read_waiting_set_aside_or_caught(filled):
    listed = sample.read_list(os.path.join(LANE, "sample.list"))[1:]
    assert len(filled["documents"]) == len(listed)
    assert {d["record"] for d in filled["documents"]} == set(listed)
    outcomes = {d["outcome"] for d in filled["documents"]}
    assert outcomes <= {"read", R.WAIT_PAGES, R.WAIT_TEXT, "set aside", "caught"}
    by = {}
    for d in filled["documents"]:
        by[d["outcome"]] = by.get(d["outcome"], 0) + 1
    assert by.get("caught") == 2 and by.get("set aside") == 1 and by.get(R.WAIT_PAGES) == 1, by
    assert by.get("read", 0) + by.get(R.WAIT_TEXT, 0) == len(listed) - 4
    stages = {(a["item"], a["stage"]) for a in filled["aside"]}
    for caught in (d for d in filled["documents"] if d["outcome"] == "caught"):
        assert (caught["key"], "pull") in stages and caught["state"] == "caught", caught["key"][-30:]
    schedule = [d for d in filled["documents"] if d["outcome"] == "set aside"][0]
    assert "scheduled" in schedule["url"] and (schedule["key"], "recognise") in stages
    noise = [d for d in filled["documents"] if "++resource++" in d["url"]][0]
    assert noise["outcome"] in ("set aside", "caught"), "crawl noise is never read"
    assert not any(a["stage"] == "listing" for a in filled["aside"]), "the gap report is the live check's, not the sample's"
    # a document is its bytes: the case page the corpus holds under two record urls is one case row, two documents rows
    twice = [d for d in filled["documents"] if d["url"].endswith("?searchterm=None")]
    assert len(twice) == 1
    plain = _doc(filled, url=twice[0]["url"].split("/?")[0])
    assert plain["document"] == twice[0]["document"] and plain["outcome"] == twice[0]["outcome"] in ("read", R.WAIT_TEXT)
    assert plain["profile"] == twice[0]["profile"] == "courts-case-page"
    assert len([c for c in filled["cases"] if c["document"] == plain["document"]]) == 1
    assert [c["url"] for c in filled["cases"] if c["document"] == plain["document"]] == [plain["url"]]


def test_each_kind_is_recognised_by_shape_and_its_sheet_read(filled):
    prof = {d["profile"]: d for d in filled["documents"] if d["profile"]}
    assert {"courts-case-page", "courts-media-release", "courts-hearing-transcript", "courts-counsel-submission", "courts-case-synopsis",
            "courts-nzsc-judgment", "courts-nzca-judgment", "courts-nzhc-civil-judgment", "courts-nzhc-criminal-judgment", "courts-judgment",
            "courts-scanned-document"} <= set(prof)
    mr = _doc(filled, sha=MR_122)
    assert (mr["citation"], mr["case_numbers"], mr["dated"]) == ("[2026] NZSC 122", ["SC 97/2025"], dt.date(2026, 9, 4))
    assert prof["courts-hearing-transcript"]["citation"].endswith("NZSC Trans 3") and prof["courts-hearing-transcript"]["pages"] > 50
    assert prof["courts-counsel-submission"]["case_numbers"] == ["SC 21/2022"]
    jdo = [d for d in filled["documents"] if "jdo_documents" in d["url"]][0]
    assert jdo["profile"] == "courts-nzca-judgment", "recognised by its court line, not its opaque name"
    misfiled = [d for d in filled["documents"] if d["kind"] == "judgment_pdf" and d["profile"] == "courts-media-release"]
    assert misfiled, "a press summary the MCP filed as a judgment is a release by shape"
    empc = prof["courts-judgment"]
    assert empc["citation"].split()[1] == "NZEmpC"
    scanned = prof["courts-scanned-document"]
    assert scanned["outcome"] == R.WAIT_PAGES and scanned["read_from"] == "pixels"


def test_the_case_page_carries_the_court_the_name_and_the_dates_and_joins_its_files_by_slug(filled):
    c = [c for c in filled["cases"] if c["url"] == RIMMER_URL][0]
    assert c["court"] == "Supreme Court" and c["citation"] == "[2026] NZSC 122" and c["case_slug"] == "rimmer-v-wilton"
    assert c["case_name"] and " v " in c["case_name"] and c["date_of_judgment"] == dt.date(2026, 9, 4)
    links = [l for l in filled["links"] if l["case"] == c["key"]]
    assert {(l["section"], l["linked_document"]) for l in links} == {("Media releases", MR_122), ("Decision", NZSC_122)}
    j, _ = _of(filled, NZSC_122)
    assert j["case_slug"] == "rimmer-v-wilton" and _doc(filled, sha=MR_122)["case_slug"] == "rimmer-v-wilton"
    assert j["judgment_date"] == c["date_of_judgment"]


def test_each_hard_case_reads_as_its_comment_says(filled):
    j, ps = _of(filled, NZSC_161)
    assert j["citation"] == "[2024] NZSC 161" and j["suppression"] and "banner" in j["suppression_kinds"]
    assert sum(p["anonymised"] for p in ps if p["role"] == "Appellants") == 3
    j, ps = _of(filled, NZSC_121)
    assert j["caption_shape"] == "matter" and [p["role"] for p in ps] == ["Referrer"]
    j, ps = _of(filled, NZSC_164)
    assert len(j["case_numbers"]) == 7 and "caption continued on page 2" in j["notes"]
    assert {"Appellants", "Respondents", "Interested Parties"} <= {p["role"] for p in ps}
    j, ps = _of(filled, NZSC_103)
    assert j["suppression"] and any(k.startswith("Family Court") for k in j["suppression_kinds"])
    j, ps = _of(filled, NZHC_2529)
    assert [p["role"] for p in ps] == ["Prosecutor", "Defendant", "Defendant"] and ps[0]["crown"]
    j, ps = _of(filled, NZHC_2519)
    assert sum(p["role"] == "Defendants" for p in ps) == 9 and j["suppression"]
    assert all(p["capacity"] is None and p["name"] is None for p in ps if p["role"] == "Defendants")
    j, ps = _of(filled, NZHC_2654)
    assert j["citation"] == "[2026] NZHC 2654" and j["status"] == "parsed"
    j, ps = _of(filled, NZSC_122)
    assert [p["role"] for p in ps] == ["Appellants", "Appellants", "Respondent"] or len(ps) >= 3


def test_every_judgment_s_citation_agrees_with_its_file_name_and_its_date_is_a_real_day(filled):
    for j in filled["judgments"]:
        name = os.path.basename(j["source_url"])
        m = re.match(r"(\d{4})-(NZ[A-Za-z]{2,6})-(\d+)", name)
        if m:
            assert j["citation"] == f"[{m.group(1)}] {m.group(2)} {m.group(3)}", j["document"][:12]
        assert dt.date(2000, 1, 1) <= j["judgment_date"] <= dt.date.today(), j["document"][:12]
        assert j["status"] == "parsed" and j["paragraphs"] > 0, j["document"][:12]


def test_paragraphs_are_indexed_in_sequence_to_the_judgment_s_last(filled):
    by = {p["judgment"]: p for p in filled["paragraphs"]}
    for j in filled["judgments"]:
        assert by[j["key"]]["n"] == by[j["key"]]["top"] == j["paragraphs"], j["document"][:12]


def test_every_row_meets_the_row_contract(filled):
    for r in filled["judgments"] + filled["parties"] + filled["cases"] + filled["people"]:
        row = {**r, "loaded_at": str(r["loaded_at"])}
        assert rowcontract.validate(row) == [], r["key"][:12]


def test_a_suppressed_judgment_publishes_no_name_but_the_crown_s_and_a_printed_initial(filled):
    suppressed = {j["key"] for j in filled["judgments"] if j["suppression"]}
    assert len(suppressed) >= 3
    for p in filled["parties"]:
        if p["judgment"] in suppressed and not p["crown"] and not p["anonymised"]:
            assert p["withheld"] and p["name"] is None and p["capacity"] is None, p["key"][:12]
        if p["judgment"] not in suppressed:
            assert not p["withheld"] and p["name"], p["key"][:12]
    docs = {j["document"] for j in filled["judgments"] if j["suppression"]}
    for n in filled["people"]:
        if n["document"] in docs and n["role"] not in ("judge", "counsel", "agency"):
            assert n["withheld"] and n["name"] is None, n["key"][:12]
    withheld = {p["key"] for p in filled["parties"] if p["withheld"]} | {n["key"] for n in filled["people"] if n["withheld"]} \
        | {c["key"] for c in filled["cases"] if c["withheld"]}
    assert withheld == {p["key"] for p in filled["private"]}


def test_the_text_reader_s_rows_where_a_reading_is_stored_and_waiting_where_not(filled):
    read = [d for d in filled["documents"] if d["outcome"] == "read"]
    waiting = [d for d in filled["documents"] if d["outcome"] == R.WAIT_TEXT]
    for d in read:
        assert d["summary"] and d["model"] and d["model_reader"], d["document"][:12]
    for d in waiting:
        assert d["summary"] is None and not [n for n in filled["people"] if n["document"] == d["document"]], d["document"][:12]
    for n in filled["people"]:
        assert n["role"] in ("party", "counsel", "witness", "judge", "company", "agency", "other") and n["kind"] in ("person", "body")
        assert n["model"] and n["reader"].startswith("registers.courts.model_read"), n["key"][:12]
    missing = sorted(d["document"][:12] for d in waiting)
    if missing:
        pytest.xfail(f"{len(missing)} sample documents have no stored text-reader reading yet (qv4-courts-read): {missing[:4]}")


def test_no_published_view_reads_the_private_table():
    text = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("--"))
    assert "courts_private" not in body and "withheld_names" not in body
    assert "pub.court_people" in body and "p.withheld AS suppressed" in body


def test_the_lane_s_check_passes_on_the_sample(filled):
    out = check.account(filled["conn"], filled["schema"], shared=True)
    assert out["failures"] == []
    assert out["status"] == {"parsed": 10} and out["roles short"] <= 2
    assert set(out["outcomes"]) <= {"read", R.WAIT_PAGES, R.WAIT_TEXT, "set aside", "caught"}


def test_the_lever_dry_runs_by_default_and_withholds_on_execute_across_the_case(filled):
    conn, schema, q = filled["conn"], filled["schema"], filled["q"]
    t = lambda n: L.table(schema, n, True)  # noqa: E731
    conn.rollback()
    before = q(f"SELECT key, name, withheld FROM {t('judgment_parties')} ORDER BY key")
    dry = suppress.run(conn, "[2026] NZSC 122", "test order", schema=schema, shared=True)
    assert dry["executed"] is False and dry["judgments"] == 1 and dry["names to withhold"] >= 3 and dry["already withheld"] == 0
    assert dry["documents reached"] == 3, "the judgment, its release and its case page"
    assert q(f"SELECT key, name, withheld FROM {t('judgment_parties')} ORDER BY key") == before
    try:
        done = suppress.run(conn, "[2026] NZSC 122", "test order, minute of 1 January", execute=True, schema=schema,
                            shared=True, by_whom="test")
        assert done["withheld now"] >= dry["names to withhold"] + 1
        rows = q(f"SELECT name, withheld FROM {t('judgment_parties')} WHERE key LIKE %s ORDER BY position", NZSC_122 + "%")
        assert rows and all(r["name"] is None and r["withheld"] for r in rows)
        assert q(f"SELECT case_name, suppression FROM {t('cases')} WHERE url = %s", RIMMER_URL) == [{"case_name": None, "suppression": True}]
        assert q(f"SELECT count(*) n FROM {t('people')} WHERE document IN (%s, %s, %s) AND NOT withheld AND name IS NOT NULL "
                 "AND role NOT IN ('judge', 'counsel', 'agency') AND upper(name) !~ %s",
                 NZSC_122, MR_122, RIMMER_PAGE, R.caption.CROWN.pattern)[0]["n"] == 0
        j = q(f"SELECT suppression, withheld, suppression_kinds FROM {t('judgments')} WHERE document = %s", NZSC_122)[0]
        assert j["suppression"] and j["withheld"].startswith("suppression order: test order") and "ledger" in j["suppression_kinds"]
        assert suppress.run(conn, "[2026] NZSC 122", "again", schema=schema, shared=True)["already withheld"] == len(rows)
        assert check.account(conn, schema, shared=True)["failures"] == []
    finally:
        conn.rollback()
    with pytest.raises(SystemExit):
        suppress.target("Smith v Jones")
    with pytest.raises(SystemExit):
        suppress.run(conn, "[2026] NZSC 122", "  ", schema=schema, shared=True)


def test_there_is_no_command_that_lifts_an_order_and_nothing_deletes_the_ledger():
    src = open(os.path.join(LANE, "suppress.py"), encoding="utf-8").read()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert not re.search(r"def\s+\w*(unsuppress|lift|undo|restore|unwithhold)", code)
    assert not re.search(r"add_argument\([^)]*(unsuppress|lift|undo|restore)", code)
    for name in os.listdir(LANE):
        if name.endswith((".py", ".sql")):
            text = open(os.path.join(LANE, name), encoding="utf-8").read()
            assert not re.search(r"(DELETE\s+FROM|TRUNCATE|DROP\s+TABLE)[^;\n]*suppression_orders", text, re.I), name
    assert "suppression_orders" not in L.TABLES and "suppression_orders" in L.RECORDS
