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
from registers.courts import caption, check, model_read, suppress
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
#: the record whose PDF has no text layer on page 1: it waits for the page reader until the shared store holds its page
#: readings (qv4-courts-pages ran on live on 30 October 2026), then is read from pixels like any other
SCANNED_RECORD = "839d101ae7a9a7bfc66d99f71b9669d2842aebeb3fa4fc799392785c36e64a77"


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
    assert by.get("caught") == 2 and by.get("set aside") == 1, by
    assert by.get("read", 0) + by.get(R.WAIT_TEXT, 0) + by.get(R.WAIT_PAGES, 0) == len(listed) - 3
    scanned = next(d for d in filled["documents"] if d["record"] == SCANNED_RECORD)
    assert scanned["read_from"] == "pixels" and scanned["outcome"] in (R.WAIT_PAGES, "read", R.WAIT_TEXT), scanned["outcome"]
    stages = {(a["item"], a["stage"]) for a in filled["aside"]}
    for caught in (d for d in filled["documents"] if d["outcome"] == "caught"):
        assert (caught["key"], "pull") in stages and caught["state"] == "caught", caught["key"][-30:]
    schedule = [d for d in filled["documents"] if d["outcome"] == "set aside" and d["profile"] is None][0]
    assert "scheduled" in schedule["url"] and (schedule["key"], "recognise") in stages
    # the 16-page determination whose text layer numbers no paragraph: over the budget, the paragraph rule cannot split
    # it, so its profile's fallback reads it page by page (Arthur, 3 November 2026); it waits on the text reader, in pieces
    unsplit = next(d for d in filled["documents"] if d["document"] and d["document"].startswith("b969c55c2414"))
    assert unsplit["profile"] == R.ERA and unsplit["outcome"] in (R.WAIT_TEXT, "read") and unsplit["pieces"] >= 2   # read once qv4-courts-read has (4 November 2026)
    assert unsplit["text_chars"] > 34000 and unsplit["dated"] and unsplit["citation"] and (unsplit["key"], "read") not in stages
    assert not any(a["reason"].startswith("the text reader cannot read it:") for a in filled["aside"])
    # every document the text reader reads, or waits for, has its piece count by its profile's rule (the check holds it too)
    for d in filled["documents"]:
        if d["outcome"] in ("read", R.WAIT_TEXT):
            assert d["pieces"] >= 1, d["document"][:12]
            assert (d["pieces"] == 1) == (d["text_chars"] <= 34000) or d["pieces"] > 1, d["document"][:12]
    assert max(d["pieces"] or 0 for d in filled["documents"]) >= 7, "the sample holds documents read in many pieces"
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
            "courts-nzsc-judgment", "courts-nzca-judgment", "courts-nzhc-civil-judgment", "courts-nzhc-criminal-judgment",
            "courts-judgment", R.ERA, R.HRRT, R.TRIBUNAL, R.NZDC} <= set(prof)
    mr = _doc(filled, sha=MR_122)
    assert (mr["citation"], mr["case_numbers"], mr["dated"]) == ("[2026] NZSC 122", ["SC 97/2025"], dt.date(2026, 9, 4))
    transcripts = [d for d in filled["documents"] if d["profile"] == "courts-hearing-transcript"]
    assert len(transcripts) == 3 and all(t["pieces"] >= 2 for t in transcripts) and sorted(t["pages"] >= 50 for t in transcripts) == [False, True, True]
    assert sorted(bool(t["citation"] and t["citation"].endswith("NZSC Trans 3")) for t in transcripts) == [False, False, True], \
        "one carries its Trans citation; the cover-sheet one (2016) and the two-column one (2004) carry none and are transcripts by their speakers"
    subs = [d for d in filled["documents"] if d["profile"] == "courts-counsel-submission"]
    assert [(d["case_numbers"], d["outcome"] in ("read", R.WAIT_TEXT), d["pieces"]) for d in subs] == [(["SC 21/2022"], True, 4)], \
        "the 38-page submission numbers its paragraphs with a bare number two spaces before the text: four pieces (read once stored)"
    # the kinds of 30 and 31 October: each by its shape, its court code in the judgment row
    courts = {j["profile"]: j["court"] for j in filled["judgments"]}
    assert courts[R.ERA] == "NZERA" and courts[R.HRRT] == "NZHRRT" and courts[R.NZDC] == "NZACC", courts
    assert {j["court"] for j in filled["judgments"] if j["profile"] == R.TRIBUNAL} == {"NZLCDT", "NZIACDT", "NZSSAA"}
    era = [j for j in filled["judgments"] if j["profile"] == R.ERA]
    assert sum(j["suppression"] for j in era) == 1 and all(j["status"] == "parsed" for j in era), "one determination orders non-publication in its text"
    hrrt = [j for j in filled["judgments"] if j["profile"] == R.HRRT]
    assert all(j["status"] == "parsed" for j in hrrt) and sum(j["suppression"] for j in hrrt) >= 1
    jdo = [d for d in filled["documents"] if "jdo_documents" in d["url"]][0]
    assert jdo["profile"] == "courts-nzca-judgment", "recognised by its court line, not its opaque name"
    misfiled = [d for d in filled["documents"] if d["kind"] == "judgment_pdf" and d["profile"] == "courts-media-release"]
    assert misfiled, "a press summary the MCP filed as a judgment is a release by shape"
    empc = prof["courts-judgment"]
    assert empc["citation"].split()[1] == "NZEmpC"
    scanned = next(d for d in filled["documents"] if d["record"] == SCANNED_RECORD)
    assert scanned["read_from"] == "pixels"
    if scanned["outcome"] == R.WAIT_PAGES:
        assert scanned["profile"] == "courts-scanned-document", "no page reading stored: recognised by its lack of text alone"
    else:
        # the page reader's stored readings stand in for the text layer: recognised by shape and read like any other
        assert scanned["profile"] in R.JUDGMENT_SLUGS and scanned["citation"] and scanned["dated"], scanned["profile"]


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
            # the tribunals pad the number ("[2023] NZSSAA 08" is printed; the file is named -8-): the figures agree
            y, court, n = j["citation"].replace("[", "").replace("]", "").split()
            assert (y, court, int(n)) == (m.group(1), m.group(2), int(m.group(3))), j["document"][:12]
        if j["judgment_date"] is not None or j["profile"] != R.TRIBUNAL:
            assert dt.date(2000, 1, 1) <= j["judgment_date"] <= dt.date.today(), j["document"][:12]
        assert j["court"] == j["citation"].split()[1] and j["court"] == j["court"].upper().replace("NZEMPC", "NZEmpC"), j["document"][:12]
        if j["read_from"] == "pixels":
            # the page reader's text prints the caption as name over role with no BETWEEN/AND labels: the caption's
            # parties are the one thing the parse may lack there; the citation, the court and the date are read
            assert j["status"] in ("parsed", "partial") and set(j["missing"]) <= {"parties"}, j["document"][:12]
        elif j["profile"] == R.TRIBUNAL:
            # the tribunals' layouts vary (71 files of nine bodies): the citation and the court are read; parties and the date may not be
            assert set(j["missing"]) <= {"parties", "judgment_date"}, j["document"][:12]
        else:
            assert j["status"] == "parsed", j["document"][:12]
        if j["paragraphs"] == 0:
            # its text layer numbers no paragraph: the paragraphs rule could not split it either, so its profile's
            # fallback cuts it at its pages and it waits on the text reader
            doc = _doc(filled, sha=j["document"])
            # waiting, or read once qv4-courts-read has read it by the fallback (4 November 2026: b969c55c2414 was)
            assert doc["outcome"] in (R.WAIT_TEXT, "read") and doc["pieces"] >= 2 and doc["text_chars"] > 34000, j["document"][:12]


def test_paragraphs_are_indexed_in_sequence_to_the_judgment_s_last(filled):
    by = {p["judgment"]: p for p in filled["paragraphs"]}
    for j in filled["judgments"]:
        if j["paragraphs"] == 0:
            assert j["key"] not in by, j["document"][:12]
            continue
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
        if n["document"] in docs:
            if model_read.kept_under_suppression(n):
                assert not n["withheld"] and n["name"], n["key"][:12]
            else:
                assert n["withheld"] and n["name"] is None, n["key"][:12]
    withheld = {p["key"] for p in filled["parties"] if p["withheld"]} | {n["key"] for n in filled["people"] if n["withheld"]} \
        | {c["key"] for c in filled["cases"] if c["withheld"]}
    assert withheld == {p["key"] for p in filled["private"]}


def test_the_keep_rule_reads_the_same_in_python_and_in_postgres_on_every_model_read_name_and_on_the_crown_s_shapes(filled):
    """The load applies model_read.kept_under_suppression, the check and the lever model_read.kept_sql; one rule.
    Measured on every name the sample's text reader found, and on the Crown's printed shapes (no person's name)."""
    conn, schema = filled["conn"], filled["schema"]
    shapes = [("party", "Attorney-General"), ("party", "The Attorney-General of New Zealand"), ("party", "Solicitor-General"),
              ("other", "Attorney-Generals Road Trust"), ("party", "R"), ("party", "Riverside Holdings Limited"), ("party", "The Queen"),
              ("party", "The King"), ("party", "His Majesty the King"), ("party", "Police"), ("party", "New Zealand Police"),
              ("party", "Commissioner of Police"), ("company", "Crown Lane Limited"), ("witness", "A Witness"), ("judge", "Able J"),
              ("counsel", "P Q Rowe KC"), ("agency", "A City Council"), ("party", "Commissioner of Inland Revenue"), ("party", "Rex")]
    shapes += [(n["role"], n["name"]) for n in filled["people"] if n["name"]]
    rows = conn.execute(f"SELECT v.role, v.name, {model_read.kept_sql('v.')} FROM (VALUES {', '.join('(%s, %s)' for _ in shapes)}) "
                        "AS v(role, name)", tuple(x for pair in shapes for x in pair)).fetchall()
    assert tuple(rows[0][:2]) == shapes[0], "the columns come back as sent"
    assert len(rows) == len(shapes) >= 19
    disagree = [i for i, (role, name, sql) in enumerate(rows) if sql != model_read.kept_under_suppression({"role": role, "name": name})]
    assert disagree == [], f"{len(disagree)} of {len(rows)} names: python and postgres read the keep rule differently (first at index {disagree[0]})"
    kept_by = {(role, name): sql for role, name, sql in rows}
    assert kept_by[("party", "Attorney-General")] and kept_by[("party", "R")] and not kept_by[("party", "Riverside Holdings Limited")]
    assert not kept_by[("party", "Rex")] and not kept_by[("other", "Attorney-Generals Road Trust")] and kept_by[("agency", "A City Council")]
    assert check.account(conn, schema, shared=True)["failures"] == []


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
    # the one ruled view (ruling 1, 3 November 2026), by its exact text: a company's NZBN or company number for the links lane
    assert body.count(check.NUMBERS_VIEW_SQL) == 1
    body = body.replace(check.NUMBERS_VIEW_SQL, "")
    assert "courts_private" not in body and "withheld_names" not in body
    assert "pub.court_people" in body and "p.withheld AS suppressed" in body


def test_the_lane_s_check_passes_on_the_sample(filled):
    out = check.account(filled["conn"], filled["schema"], shared=True)
    assert out["failures"] == []
    assert out["status"].get("parsed") >= 15 and set(out["status"]) <= {"parsed", "partial"} and out["roles short"] <= 2
    assert set(out["roles the source's own"].values()) <= {caption.INTERVENER_UNLISTED, caption.APPEAL_UNDER_FIRST_INSTANCE}
    assert out["status"].get("partial", 0) <= 4 and all(j["profile"] in (R.TRIBUNAL, "courts-nzsc-judgment") for j in filled["judgments"] if j["status"] == "partial")
    assert out["pieces"]["total pieces"] >= 60 and out["pieces"]["documents over the budget"] >= 12 and out["pieces"]["cannot split (set aside at read)"] == 0
    assert out["pieces by profile"]["courts-hearing-transcript"] >= 10 and out["pieces by profile"]["courts-case-page"] == 3
    assert set(out["outcomes"]) <= {"read", R.WAIT_PAGES, R.WAIT_TEXT, "set aside", "caught"}


def test_a_record_the_pull_lands_after_the_load_s_stamp_is_the_next_load_s(filled):
    """The pull may land records while a load runs (4 November 2026: the 19:00 pull landed 1,950 courts records
    into the 18:14 load, and the check counted them against it). The check counts the pull's arrivals by the
    load's stamp; one landed before the stamp with no row still fails. The arrivals are a temporary table."""
    conn, schema = filled["conn"], filled["schema"]
    t = lambda n: L.table(schema, n, True)  # noqa: E731
    stamp = conn.execute(f"SELECT min(loaded_at) FROM {t('documents')}").fetchone()[0]
    keys = [r[0] for r in conn.execute(f"SELECT key FROM {t('documents')}") if not r[0].startswith(check.capture.OWN_PREFIX)]
    assert stamp is not None and keys
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS arrivals (corpus text, seq bigint, record_id text, url text, sha256 text, "
                 "landed_at timestamptz)")
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS files (corpus text, record_sha256 text, content_type text, capture_sha256 text, "
                 "state text, bytes bigint)")
    temp = conn.execute("SELECT pg_my_temp_schema()::regnamespace::text").fetchone()[0]
    def failures(late_at):
        conn.execute("DELETE FROM pg_temp.arrivals")
        rows = [(k, stamp - dt.timedelta(hours=1)) for k in keys] + [("a-record-landed-late", late_at)]
        for i, (k, at) in enumerate(rows):
            conn.execute("INSERT INTO pg_temp.arrivals VALUES (%s, %s, %s, NULL, %s, %s)", (check.capture.CORPUS, i, k, "0" * 64, at))
        # the load reads by the same stamp: the late record is not among its entries
        got = {e["record_id"] for e in check.capture.records(conn, temp, until=stamp)}
        assert ("a-record-landed-late" in got) == (late_at <= stamp) and set(keys) <= got
        return [f for f in check.account(conn, schema, shared=True, mcp_schema=temp)["failures"] if "the pull took" in f]
    assert failures(stamp + dt.timedelta(minutes=1)) == []
    assert failures(stamp - dt.timedelta(minutes=1)) == [f"the pull took {len(keys) + 1} records, the lane has {len(keys)} document rows from it"]
    conn.execute("DELETE FROM pg_temp.arrivals")


def test_the_load_s_table_check_holds_no_lock_on_the_own_capture_s_ledger(filled):
    """The load makes its tables where absent and commits, so the hour it reads holds no share lock that blocks the
    own capture's insert into own_files (5 November 2026: the JDO capture cancelled at 05:29 behind the 05:24 load)."""
    conn, schema = filled["conn"], filled["schema"]
    conn.commit()
    L.ensure_record(conn, schema, shared=True)
    held = conn.execute("SELECT l.relation::regclass::text, l.mode FROM pg_locks l WHERE l.pid = pg_backend_pid() "
                        "AND l.relation IS NOT NULL AND l.mode = 'ShareLock'").fetchall()
    assert held == []
    assert conn.execute("SELECT to_regclass(%s)", (L.table(schema, "own_files", True),)).fetchone()[0] is not None


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
                 f"AND NOT {model_read.kept_sql()}", NZSC_122, MR_122, RIMMER_PAGE)[0]["n"] == 0
        j = q(f"SELECT suppression, withheld, suppression_kinds FROM {t('judgments')} WHERE document = %s", NZSC_122)[0]
        assert j["suppression"] and j["withheld"].startswith("suppression order: test order") and "ledger" in j["suppression_kinds"]
        assert suppress.run(conn, "[2026] NZSC 122", "again", schema=schema, shared=True)["already withheld"] == len(rows)
        # ruling 142: every name the order covers is kept whole beside its row with the order's words; a counsel's
        # party acted for is never lost
        W = L.table(schema + "_private", "withheld_names", True)
        kept = q(f"SELECT w.held_in, w.suppressed, w.suppression_words, w.name <> '' AS named FROM {W} w JOIN "
                 f"{t('judgment_parties')} p ON p.key = w.key WHERE p.key LIKE %s", NZSC_122 + "%")
        assert len(kept) == len(rows) and all(k["named"] and k["suppressed"] and k["held_in"] == "judgment_parties"
                                              for k in kept)
        assert all(k["suppression_words"].startswith("suppression order: test order") for k in kept)
        assert q(f"SELECT count(*) n FROM {t('people')} p WHERE p.withheld AND p.name IS NULL AND NOT EXISTS "
                 f"(SELECT 1 FROM {W} w WHERE w.key = p.key AND w.held_in = 'people')")[0]["n"] == 0
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


def _ids(filled):
    return filled["q"](f"SELECT * FROM {L.table(filled['schema'] + '_private', 'identifiers', True)} ORDER BY key")


def test_the_identifying_details_are_gathered_privately_by_shape_on_the_real_sample(filled):
    """Arthur, 3 November 2026: any identifying information, gathered beside the names. Counts only on failure."""
    from registers.courts import identifiers as I
    ids = _ids(filled)
    kinds = {}
    for r in ids:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    assert len(ids) >= 20 and {"email", "phone"} <= set(kinds), kinds
    docs = {d["document"] for d in filled["documents"]}
    assert all(r["document"] in docs and r["kind"] in I.KINDS and r["value"] and r["person"] is None for r in ids)
    assert len({(r["document"], r["kind"], r["value"].upper()) for r in ids}) == len(ids), "a detail once per document"
    # gathered under a suppression too: the private table is not thinned by the withholding
    suppressed = {j["document"] for j in filled["judgments"] if j["suppression"]}
    assert any(r["document"] in suppressed for r in ids), "a suppressed judgment's details are gathered privately"
    out = check.account(filled["conn"], filled["schema"], shared=True)
    assert out["failures"] == [] and out["identifiers"].get("email") == kinds["email"]


def test_no_identifying_detail_reaches_a_table_a_published_view_reads(filled):
    """Every text value of every reading table (the pub views select only from these) against the fixed-shape details."""
    strong = {r["value"] for r in _ids(filled) if r["kind"] in ("email", "phone", "address", "po_box", "nzbn")}
    assert strong
    leaks = 0
    for t in L.TABLES:
        for row in filled["q"](f"SELECT * FROM {L.table(filled['schema'], t, True)}"):
            for col, v in row.items():
                if col in ("key", "url", "href", "label") or not isinstance(v, str):
                    continue      # an address's key, a link's own url and label are the court's, not a detail
                leaks += sum(1 for s in strong if s in v)
    assert leaks == 0, f"{leaks} identifying detail(s) inside a reading table"


def test_the_check_fails_an_identifier_column_or_a_published_view_on_the_private_schema(filled):
    conn, schema = filled["conn"], filled["schema"]
    conn.rollback()
    try:
        conn.execute(f"ALTER TABLE {L.table(schema, 'people', True)} ADD COLUMN email text")
        assert any("has a column 'email'" in f for f in check.account(conn, schema, shared=True)["failures"])
    finally:
        conn.rollback()
    try:
        conn.execute("CREATE SCHEMA IF NOT EXISTS pub")
        conn.execute(f"CREATE VIEW pub.court_leak_test AS SELECT kind FROM {L.table(schema + '_private', 'identifiers', True)}")
        assert any("reads the private schema" in f for f in check.account(conn, schema, shared=True)["failures"])
    finally:
        conn.rollback()


def test_the_lever_leaves_the_private_details_whole_and_publishes_none(filled):
    conn, schema, q = filled["conn"], filled["schema"], filled["q"]
    conn.rollback()
    before = len(_ids(filled))
    try:
        suppress.run(conn, "[2026] NZSC 122", "test order", execute=True, schema=schema, shared=True, by_whom="test")
        assert len(_ids(filled)) == before
        assert check.account(conn, schema, shared=True)["failures"] == []
    finally:
        conn.rollback()
