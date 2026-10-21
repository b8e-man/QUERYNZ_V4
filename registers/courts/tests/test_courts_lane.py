"""The courts lane on its filled sample (the documents sample.list names,
read through this branch's code): every listed document accounted for, each
hard case read as its comment in sample.list says, the row contract, the
suppression rule on real judgments, the lane's check, and the lever. These
tests read real documents and can fail against them. No model; nothing
fetched. A failure message names a document by its hash and never prints a
name from a judgment."""
import datetime as dt
import os
import re

import pytest

from support import db, lane, rowcontract, sample
from registers.courts import check, suppress
from registers.courts import load as L

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "courts")
NZSC_161 = "af540a6a0ab85a307c5e0206e41be2221e52e133dcf9dbe2b6dd60b81282f05e"
NZCA_15 = "d2e3a5d946d936749539b2eee9418cf50855c37eebe724fb495d2a521cfef208"
NZCA_1 = "6e35522ee40f429781a17d9bf3be184fcc2d443fbfbe8d2f369a9786b200486b"
NZSC_121 = "f302207384b38cdbb12af638f39f89f6fa35571c6141c393287db8c2bf8df8a8"
NZSC_164 = "04ccbc867b422d5886ed2a06cd4a0f576289f37d0f17f2343f77b1fbdc04a7a8"
NZHC_1303 = "fb9197201dfdf31f43a66146a66442e3c4d49204b945fc3638c5b69ae59b9c10"
NZHC_2529 = "8af5489fbd83ff36287f9ac52d0cf51dfc02ec0e98266021ea56ce1daadbb1c3"
NZHC_101 = "b1d094e34628958bcfd780e3d46a4772d5c9a34aff1491a6c63349d0f0688a26"
NZHC_2279 = "2143318967aff11ba0a39ab78f45fa2217d68aeeba7458228ea47655fa224b4f"
NZHC_472 = "872671193e7f06f633a7276ea89f7a6a9a96d79432b33144f41eaf69120bad77"
NZHC_2519 = "28e91d9a66421fcc966b2d9ce4a39e2c6d18f4dc7ebe94859f47e3601721e09c"
REISSUE = ("13680ffdb6b04a61ffbb4a591f89545fce77479750667eafba0d14ebb32f9423",
           "4122a601be9fe02a641c7d04b74c18cfc43f80216afdf95ad31b59b4dec6dff4")
GONE = "50dc03de8f93f75ece612a5ee085858fbbcddb46b9ef9bb63cab732801b5cff9"
WAITANGI = "8008bd12a3d512ed47a2c5fec658ef1f7915877a9f30b0c6af5d60c49a92e62b"


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
               "judgments": q(f"SELECT * FROM {t('judgments')} ORDER BY key"),
               "parties": q(f"SELECT * FROM {t('judgment_parties')} ORDER BY key"),
               "files": q(f"SELECT * FROM {t('files')}"),
               "aside": q(f"SELECT * FROM {t('set_aside')}"),
               "paragraphs": q(f"SELECT judgment, count(*) n, max(number) top FROM {t('paragraphs')} GROUP BY 1"),
               "private": q(f"SELECT key, capacity IS NOT NULL AS capacity FROM {L.table(schema + '_private', 'withheld_names', True)}")}


def _of(filled, sha):
    j = [x for x in filled["judgments"] if x["document"] == sha]
    return j[0] if j else None, [p for p in filled["parties"] if p["key"].startswith(sha)]


def test_every_listed_document_is_a_judgment_or_a_catch_log_line(filled):
    listed = set(sample.read_list(os.path.join(LANE, "sample.list"))[1:])
    judged = {j["document"] for j in filled["judgments"]}
    aside = {a["item"] for a in filled["aside"] if a["stage"] in ("capture", "recognise")}
    assert listed == judged | aside and not judged & aside
    assert {f["document"] for f in filled["files"]} == listed
    assert [a["reason"][:9] for a in filled["aside"] if a["item"] == GONE] == ["not held:"]
    assert any(a["item"] == WAITANGI and "Waitangi" in a["reason"] for a in filled["aside"])


def test_each_case_reads_as_its_comment_says(filled):
    j, ps = _of(filled, NZSC_161)
    assert j["citation"] == "[2024] NZSC 161" and j["suppression"] and "banner" in j["suppression_kinds"]
    assert sum(p["anonymised"] for p in ps if p["role"] == "Appellants") == 3
    j, ps = _of(filled, NZCA_1)
    assert [p["role"] for p in ps] == ["Appellant", "Respondent"] and not j["suppression"]
    assert len(ps[0]["name"].split()) >= 6, "a singular role's four wrapped lines are one name"
    j, ps = _of(filled, NZSC_121)
    assert j["caption_shape"] == "matter" and [p["role"] for p in ps] == ["Referrer"]
    j, ps = _of(filled, NZSC_164)
    assert len(j["case_numbers"]) == 7 and "caption continued on page 2" in j["notes"]
    assert {"Appellants", "Respondents", "Interested Parties"} <= {p["role"] for p in ps}
    assert any(p["confidence"] == "low" for p in ps)
    j, ps = _of(filled, NZHC_1303)
    assert [(p["role"], p["anonymised"]) for p in ps] == [("Prosecutor", False)] + [("Defendant", True)] * 3
    assert ps[0]["crown"] and ps[0]["name"] == "THE KING"
    j, ps = _of(filled, NZHC_2529)
    assert [p["role"] for p in ps] == ["Prosecutor", "Defendant", "Defendant"]
    j, ps = _of(filled, NZHC_101)
    assert sum(p["role"] == "Defendant" for p in ps) == 3
    j, ps = _of(filled, NZHC_2279)
    assert [p["role"] for p in ps][:2] == ["First Plaintiff", "Second Plaintiff"] and len(ps) == 6
    j, ps = _of(filled, NZHC_472)
    assert {"Second Respondent", "Third Respondent"} <= {p["role"] for p in ps}
    j, ps = _of(filled, NZHC_2519)
    assert sum(p["role"] == "Defendants" for p in ps) == 9 and j["suppression"]
    assert all(p["capacity"] is None and p["name"] is None for p in ps if p["role"] == "Defendants")
    a, b = (_of(filled, s)[0] for s in REISSUE)
    assert a["citation"] == b["citation"] and a["key"] != b["key"]


def test_every_judgment_s_citation_agrees_with_its_file_name_and_its_date_is_a_real_day(filled):
    for j in filled["judgments"]:
        name = os.path.basename(j["source_url"])
        m = re.match(r"(\d{4})-(NZ[A-Z]{2})-(\d+)", name)
        assert j["citation"] == f"[{m.group(1)}] {m.group(2)} {m.group(3)}", j["document"][:12]
        assert dt.date(2000, 1, 1) <= j["judgment_date"] <= dt.date.today(), j["document"][:12]
        assert j["status"] == "parsed" and j["paragraphs"] > 0, j["document"][:12]


def test_paragraphs_are_indexed_in_sequence_to_the_judgment_s_last(filled):
    by = {p["judgment"]: p for p in filled["paragraphs"]}
    for j in filled["judgments"]:
        assert by[j["key"]]["n"] == by[j["key"]]["top"] == j["paragraphs"], j["document"][:12]


def test_every_row_meets_the_row_contract(filled):
    for r in filled["judgments"] + filled["parties"]:
        row = {**r, "loaded_at": str(r["loaded_at"])}
        assert rowcontract.validate(row) == [], r["key"][:12]


def test_a_suppressed_judgment_publishes_no_name_but_the_crown_s_and_a_printed_initial(filled):
    suppressed = {j["key"] for j in filled["judgments"] if j["suppression"]}
    assert len(suppressed) >= 5
    for p in filled["parties"]:
        if p["judgment"] in suppressed and not p["crown"] and not p["anonymised"]:
            assert p["withheld"] and p["name"] is None and p["capacity"] is None, p["key"][:12]
        if p["judgment"] not in suppressed:
            assert not p["withheld"] and p["name"], p["key"][:12]
    withheld = {p["key"] for p in filled["parties"] if p["withheld"]}
    assert withheld == {p["key"] for p in filled["private"]}
    j, ps = _of(filled, NZCA_15)
    assert [p["name"] is None for p in ps] == [True, False] and ps[1]["crown"]


def test_no_published_view_reads_the_private_table():
    text = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("--"))
    assert "courts_private" not in body and "withheld_names" not in body


def test_the_lane_s_check_passes_on_the_sample(filled):
    out = check.account(filled["conn"], filled["schema"], shared=True)
    assert out["failures"] == []
    assert out["status"] == {"parsed": 15} and out["roles short"] <= 1


def test_the_lever_dry_runs_by_default_and_withholds_on_execute(filled):
    conn, schema, q = filled["conn"], filled["schema"], filled["q"]
    t = lambda n: L.table(schema, n, True)  # noqa: E731
    conn.rollback()
    before = q(f"SELECT key, name, withheld FROM {t('judgment_parties')} ORDER BY key")
    dry = suppress.run(conn, "[2025] NZCA 1", "test order", schema=schema, shared=True)
    assert dry == {"ref": "[2025] NZCA 1", "executed": False, "judgments": 1, "names to withhold": 2, "already withheld": 0}
    assert q(f"SELECT key, name, withheld FROM {t('judgment_parties')} ORDER BY key") == before
    try:
        done = suppress.run(conn, "[2025] NZCA 1", "test order, minute of 1 January", execute=True, schema=schema,
                            shared=True, by_whom="test")
        assert done["withheld now"] == 2
        rows = q(f"SELECT role, name, withheld FROM {t('judgment_parties')} WHERE key LIKE %s ORDER BY position", NZCA_1 + "%")
        assert rows == [{"role": "Appellant", "name": None, "withheld": True},
                        {"role": "Respondent", "name": None, "withheld": True}]
        j = q(f"SELECT suppression, withheld, suppression_kinds FROM {t('judgments')} WHERE document = %s", NZCA_1)[0]
        assert j["suppression"] and j["withheld"].startswith("suppression order: test order") and "ledger" in j["suppression_kinds"]
        assert q(f"SELECT count(*) n FROM {L.table(schema + '_private', 'withheld_names', True)} WHERE key LIKE %s",
                 NZCA_1 + "%")[0]["n"] == 2
        assert suppress.run(conn, "[2025] NZCA 1", "again", schema=schema, shared=True)["already withheld"] == 2
        assert check.account(conn, schema, shared=True)["failures"] == []
    finally:
        conn.rollback()
    with pytest.raises(SystemExit):
        suppress.target("Smith v Jones")
    with pytest.raises(SystemExit):
        suppress.run(conn, "[2025] NZCA 1", "  ", schema=schema, shared=True)


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
