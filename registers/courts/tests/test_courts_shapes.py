"""Recognition by shape, the case page, the sheets, the text reader's
answer and the suppression of model-read names, on invented pages shaped
like the corpus's files (every name and number here is invented). No
database, no model, nothing fetched. A mutant check breaks read.recognise
on purpose and asserts these properties catch it."""
import json
import os
import re
import sys
import tempfile

import pytest

from support import reader as rd
from registers.courts import capture as C
from registers.courts import model_read as M
from registers.courts import read as R

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L, N = " " * 15, " " * 44
SHA = "ab" * 32
SHA2 = "cd" * 32
SHA3 = "ef" * 32


def page(*lines):
    return "\n".join(lines) + "\n"


JUDGMENT = page("IN THE SUPREME COURT OF NEW ZEALAND", "I TE KŌTI MANA NUI O AOTEAROA", " " * 70 + "SC 12/2099",
                " " * 66 + "[2099] NZSC 7", L + "BETWEEN" + " " * 22 + "EXAMPLE HOLDINGS LIMITED", N + "Appellant",
                L + "AND" + " " * 26 + "SAMPLE PERSON", N + "Respondent", "Hearing:             13 June 2098",
                "Court:               Able CJ, Baker and Carter JJ", "Counsel:             P Q Rowe KC for Appellant",
                "                     S T Vale for Respondent", "Judgment:            28 November 2099",
                "                 JUDGMENT OF THE COURT", "   A   The appeal is dismissed.", "[1]  The first paragraph.", "[2]  The second.")
OLD_JUDGMENT = page("IN THE COURT OF APPEAL OF NEW ZEALAND", " " * 70 + "CA94/05", " " * 66 + "[2007] NZCA 61",
                    L + "BETWEEN" + " " * 22 + "EXAMPLE TRADING LIMITED", N + "Appellant", L + "AND" + " " * 26 + "A PERSON", N + "Respondent",
                    "Hearing:          30 November 2006", "Court:            Young P, Dunn and Evans JJ", "Counsel:          B P Henry for Appellant",
                    "Judgment:         12 March 2007", "            JUDGMENT OF THE COURT")
EMPC = page("IN THE EMPLOYMENT COURT OF NEW ZEALAND", "AUCKLAND", " " * 66 + "[2099] NZEmpC 192", " " * 70 + "EMPC 230/2098",
            L + "IN THE MATTER OF" + " " * 12 + "a challenge", L + "BETWEEN" + " " * 22 + "A UNION INCORPORATED", N + "Plaintiff",
            "Hearing:             13 June 2099", "Appearances:         P Cranney, counsel for plaintiff", "Judgment:            25 October 2099",
            "                     JUDGMENT OF CHIEF JUDGE EXAMPLE")
RELEASE = page("4 SEPTEMBER 2099", "MEDIA RELEASE", "EXAMPLE HOLDINGS LIMITED v SAMPLE PERSON", "(SC 12/2099)          [2099] NZSC 7",
               "PRESS SUMMARY", "This summary is provided to assist in the understanding of the Court's judgment. It does not",
               "comprise part of the reasons for that judgment.", "What this judgment is about", "The appeal concerned a deposit.")
TRANSCRIPT = page("IN THE SUPREME COURT OF NEW ZEALAND", " " * 70 + "SC 12/2099", " " * 60 + "[2099] NZSC Trans 9",
                  L + "BETWEEN" + " " * 22 + "EXAMPLE HOLDINGS LIMITED", N + "Appellant", "Hearing:    13 June 2099",
                  "Court:      Able CJ, Baker and Carter JJ", "Counsel:    P Q Rowe KC for Appellant", "ABLE CJ:", "Yes Mr Rowe.",
                  "MR ROWE KC:", "May it please the Court.")
SUBMISSION = page("IN THE SUPREME COURT OF NEW ZEALAND", "I TE KŌTI MANA NUI O AOTEAROA", " " * 70 + "SC 21/2099",
                  L + "BETWEEN" + " " * 22 + "EXAMPLE HOLDINGS LIMITED", N + "Appellant", L + "AND" + " " * 26 + "SAMPLE PERSON", N + "Respondent",
                  "________________________________________", "SUBMISSIONS OF COUNSEL FOR THE APPELLANT", "Next event date: 8 June 2099",
                  "________________________________________", "Counsel acting: P Q Rowe KC", "1. These submissions address the appeal.")
SYNOPSIS = page("Supreme Court of New Zealand", "Te Kōti Mana Nui", "8 November 2099", "CASE SYNOPSIS", "EXAMPLE HOLDINGS LIMITED v SAMPLE PERSON",
                "(SC 49/2099)", "This synopsis is provided to assist in understanding the history of the case and the issues to be heard.")
SCHEDULE = page("THE EMPLOYMENT COURT OF NEW ZEALAND", "TE KŌTI TAKE MAHI O AOTEAROA", "SCHEDULE OF CASES", "26 October 2099 – 6 November 2099",
                "Courtroom    Tuesday    Example v Sample    Judge Able")
CASE_PAGE = """<html><head><title>Example v Sample  [2099] NZSC 7 &mdash; Courts of New Zealand</title></head><body><nav>menu</nav>
<main id="main" class="main"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="/">Home</a></li>
<li class="breadcrumb-item"><a href="/the-courts">The courts</a></li><li class="breadcrumb-item"><a href="/the-courts/supreme-court">Supreme Court</a></li>
<li class="breadcrumb-item active">Example v Sample</li></ol>
<h1 class="case__title">
Example v Sample -
[2099] NZSC 7
</h1>
<h2 class="h3 case__sub-heading">Media releases</h2><ul><li><a href="/assets/cases/2099/MR-2099-NZSC-7.pdf">MR [2099] NZSC 7 (PDF 250 KB)</a></li></ul>
<h2 class="h3 case__sub-heading">Summary</h2><div class="case__summary">Civil Appeal - a deposit</div>
<h2 class="h3 case__sub-heading">Result</h2><div class="case__result">A The appeal is dismissed.<br>B Costs to the respondent.</div>
<h2 class="h3 case__sub-heading">Date of Hearing</h2><p class="case__date">13 June 2098</p>
<h2 class="h3 case__sub-heading">Date of Judgment</h2><p class="case__date">28 November 2099</p>
<h2 class="h3 case__sub-heading">Judges</h2><p class="case__judges">Able CJ, Baker and Carter JJ</p>
<h2 class="h3 case__sub-heading">Decision</h2><ul><li><a href="/assets/cases/2099/2099-NZSC-7.pdf">Example v Sample (PDF 300 KB)</a></li></ul>
<h2 class="h3 case__sub-heading">Related Documents</h2><p class="case__related-decision"><span>High Court decision</span> — <a href="https://www.justice.govt.nz/jdo_documents/workspace___SpacesStore_0000.pdf">Example v Sample [2097] NZHC 1</a></p>
</main></body></html>"""
NOISE = "<html><head><title>Courts</title></head><body><form id=\"sendto_form\">send to a friend</form></body></html>"
URL = "https://www.courtsofnz.govt.nz/cases/example-v-sample"


def _texts(p1, p2=""):
    return {1: p1, 2: p2}


def test_each_shape_is_recognised_by_what_its_pages_print_never_by_its_name():
    e = {"url": "https://www.courtsofnz.govt.nz/assets/x/opaque-name.pdf", "kind": "judgment_pdf"}
    pdf = b"%PDF-1.4 fake"
    assert R.recognise(e, pdf, _texts(JUDGMENT))[0] == "courts-nzsc-judgment"
    assert R.recognise(e, pdf, _texts(OLD_JUDGMENT))[0] == "courts-nzca-judgment"
    assert R.recognise(e, pdf, _texts(EMPC))[0] == "courts-judgment"
    assert R.recognise(e, pdf, _texts(RELEASE))[0] == "courts-media-release"
    assert R.recognise(e, pdf, _texts(TRANSCRIPT))[0] == "courts-hearing-transcript"
    assert R.recognise(e, pdf, _texts(SUBMISSION))[0] == "courts-counsel-submission"
    assert R.recognise(e, pdf, _texts(SYNOPSIS))[0] == "courts-case-synopsis"
    assert R.recognise(e, pdf, _texts(""))[0] == "courts-scanned-document"
    assert R.recognise(e, pdf, _texts(SCHEDULE)) == (None, "no shape recognised: not a judgment, release, transcript, submission, synopsis or case page")
    assert R.recognise({"url": URL}, CASE_PAGE.encode())[0] == "courts-case-page"
    assert R.recognise({"url": URL + "/sendto_form"}, NOISE.encode())[0] is None
    # the High Court's two profiles by the case number's prefix
    hc = JUDGMENT.replace("SUPREME COURT", "HIGH COURT").replace("SC 12/2099", "CIV-2099-404-000001")
    assert R.recognise(e, pdf, _texts(hc))[0] == "courts-nzhc-civil-judgment"
    assert R.recognise(e, pdf, _texts(hc.replace("CIV-2099", "CRI-2099")))[0] == "courts-nzhc-criminal-judgment"


def test_the_case_page_gives_the_court_the_name_the_dates_and_its_links():
    p = R.case_page(CASE_PAGE.encode(), URL)
    assert p["case_name"] == "Example v Sample" and p["citation"] == "[2099] NZSC 7" and p["court"] == "Supreme Court"
    assert p["sections"]["Result"].startswith("A The appeal is dismissed.") and p["sections"]["Summary"] == "Civil Appeal - a deposit"
    assert R._case_date(p["sections"]["Date of Judgment"]).isoformat() == "2099-11-28"
    assert R._case_date(p["sections"]["Date of Hearing"]).isoformat() == "2098-06-13"
    assert [(s, h.rsplit("/", 1)[1]) for s, _, h in p["links"]] == [("Media releases", "MR-2099-NZSC-7.pdf"), ("Decision", "2099-NZSC-7.pdf"),
                                                                    ("Related Documents", "workspace___SpacesStore_0000.pdf")]
    assert p["links"][0][2].startswith("https://www.courtsofnz.govt.nz/assets/"), "a relative link is made absolute on the page's host"
    assert R.case_page(NOISE.encode(), URL) is None


def test_a_sheet_reads_its_citation_case_numbers_and_date():
    s = R.sheet(_texts(RELEASE), R.RELEASE)
    assert (s["citation"], s["case_numbers"], s["dated"].isoformat(), s["suppression"]) == ("[2099] NZSC 7", ["SC 12/2099"], "2099-09-04", False)
    t = R.sheet(_texts(TRANSCRIPT), R.TRANSCRIPT)
    assert t["citation"] == "[2099] NZSC Trans 9" and t["case_numbers"] == ["SC 12/2099"]
    assert R.sheet(_texts(SUBMISSION), R.SUBMISSION)["dated"].isoformat() == "2099-06-08"


def test_the_text_reader_s_answer_is_taken_only_as_a_checked_json_object():
    assert M.parse_answer("no object here") is None
    assert M.parse_answer('{"summary": "x"}') is None, "no people list: not a reading"
    got = M.parse_answer('Sure. {"summary": "An appeal about a deposit.", "people": [{"name": "Sample Person", "kind": "person", "role": "party", "role_text": "respondent"}, '
                         '{"name": "P Q Rowe KC", "role": "counsel", "for": "Example Holdings Limited"}, {"name": "", "role": "judge"}, '
                         '{"name": "Example Holdings Limited", "role": "company"}, {"name": "Able CJ", "role": "chief justice"}]} thanks')
    assert got["summary"] == "An appeal about a deposit."
    assert [(p["name"], p["kind"], p["role"], p["for"]) for p in got["people"]] == [
        ("Sample Person", "person", "party", None), ("P Q Rowe KC", "person", "counsel", "Example Holdings Limited"),
        ("Example Holdings Limited", "body", "company", None), ("Able CJ", "person", "other", None)]
    assert len(M.excerpt({1: "a" * 50000, 2: "b" * 10000})) < 50000 + 10000, "a long document is sent as its head and its tail"


def _fake_store(tmp, docs: dict):
    """A reader store holding one text reader's reading per document, as read_one would store it."""
    store = rd.Store(tmp)
    for sha, (slug, answer) in docs.items():
        version = R.profile_version(slug)
        store.put(rd.Reading(sha, 1, M.READER, M.TEXT_MODEL, M.settings(), slug, version, "text",
                             json.dumps(answer), rows=answer["people"], made_at="2099-01-01T00:00:00+13:00"))
    return store


def _entries():
    base = {"source": "query-nz", "note": "test", "state": "landed", "content_type": "application/pdf", "fetched_at": None}
    return [{**base, "record_id": "u1", "record": "1" * 64, "seq": 1, "kind": "judgment_pdf", "case_slug": "example-v-sample",
             "url": "https://www.courtsofnz.govt.nz/assets/cases/2099/2099-NZSC-7.pdf", "capture": SHA},
            {**base, "record_id": "u2", "record": "2" * 64, "seq": 2, "kind": "media_release", "case_slug": "example-v-sample",
             "url": "https://www.courtsofnz.govt.nz/assets/cases/2099/MR-2099-NZSC-7.pdf", "capture": SHA2},
            {**base, "record_id": "u3", "record": "3" * 64, "seq": 3, "kind": "case_page", "case_slug": "example-v-sample",
             "url": URL, "capture": SHA3, "content_type": "text/html"},
            {**base, "record_id": "u4", "record": "4" * 64, "seq": 4, "kind": "judgment_pdf", "case_slug": "other", "state": "caught",
             "url": "https://www.courtsofnz.govt.nz/assets/cases/2099/2099-NZSC-8.pdf", "capture": "5" * 64}]


def _pdf_bytes(text):
    """The reading takes a PDF's text through pdftotext; the tests hand it the page map instead by patching."""
    return b"%PDF-1.4\n" + text.encode()


def test_a_suppressed_judgment_withholds_the_model_read_names_on_every_document_of_its_case(monkeypatch):
    banner = "NOTE: ORDER PROHIBITING PUBLICATION OF NAME OF RESPONDENT.\n"
    pages = {SHA: {1: banner + JUDGMENT}, SHA2: {1: RELEASE}}
    monkeypatch.setattr(R, "_texts_of", lambda data, sha, store, v: (pages[sha], "text", []))
    monkeypatch.setattr(R, "page_total", lambda data: 1)
    import support.docread.read as DR
    monkeypatch.setattr(DR, "read_document", lambda *a, **k: None)
    people = [{"name": "Sample Person", "kind": "person", "role": "party", "role_text": "respondent", "for": None},
              {"name": "Able CJ", "kind": "person", "role": "judge", "role_text": "judge", "for": None},
              {"name": "P Q Rowe KC", "kind": "person", "role": "counsel", "role_text": "counsel", "for": "Example Holdings Limited"},
              {"name": "Example Holdings Limited", "kind": "body", "role": "company", "role_text": "appellant", "for": None},
              {"name": "The King", "kind": "body", "role": "party", "role_text": "prosecutor", "for": None}]
    data = {SHA: _pdf_bytes(JUDGMENT), SHA2: _pdf_bytes(RELEASE), SHA3: CASE_PAGE.encode()}
    with tempfile.TemporaryDirectory() as td:
        store = _fake_store(td, {SHA: ("courts-nzsc-judgment", {"summary": "A judgment.", "people": people}),
                                 SHA2: ("courts-media-release", {"summary": "A release.", "people": people[:1]}),
                                 SHA3: ("courts-case-page", {"summary": "A case page.", "people": people[:1]})})
        res = R.read(_entries(), [], store=store, data_of=lambda sha: data.get(sha))
    assert res.counts["records"] == 4 and res.counts["read"] == 3 and res.counts["caught"] == 1
    j = res.judgments[0]
    assert j["suppression"] and "banner" in j["suppression_kinds"]
    byname = {(p["document"][:2], p["key"].rsplit("/", 1)[1]): p for p in res.people}
    assert byname[("ab", "1")]["name"] is None and byname[("ab", "1")]["withheld"] and byname[("ab", "1")]["role"] == "party"
    assert byname[("ab", "4")]["name"] is None, "a body that is a party is withheld too"
    assert byname[("ab", "2")]["name"] == "Able CJ" and byname[("ab", "3")]["name"] == "P Q Rowe KC"
    assert byname[("ab", "5")]["name"] == "The King", "the Crown is never withheld"
    assert byname[("cd", "1")]["name"] is None, "the release of the same citation is reached"
    assert byname[("ef", "1")]["name"] is None, "the case page of the same case is reached"
    assert res.cases[0]["case_name"] is None and res.cases[0]["suppression"]
    withheld = {k for k, _, _ in res.withheld}
    assert withheld == {p["key"] for p in res.people if p["withheld"]} | {p["key"] for p in res.parties if p["withheld"]} | {res.cases[0]["key"]}
    doc = {d["document"]: d for d in res.documents}
    assert doc[SHA]["summary"] == "A judgment." and doc[SHA]["model"] == M.TEXT_MODEL and doc[SHA]["outcome"] == "read"
    assert res.case_links[1]["linked_document"] == SHA, "a case page's Decision link is joined to the corpus document by url"
    assert res.counts["set_aside"] == 1 and res.set_aside[0][1] == "pull"


def test_without_a_stored_model_reading_the_document_waits_and_nothing_is_asked(monkeypatch):
    monkeypatch.setattr(R, "_texts_of", lambda data, sha, store, v: ({1: JUDGMENT}, "text", []))
    monkeypatch.setattr(R, "page_total", lambda data: 1)
    import support.docread.read as DR
    monkeypatch.setattr(DR, "read_document", lambda *a, **k: None)
    monkeypatch.setattr(M, "ask", lambda *a, **k: pytest.fail("the load asked a model"))
    with tempfile.TemporaryDirectory() as td:
        res = R.read(_entries()[:1], [], store=rd.Store(td), data_of=lambda sha: _pdf_bytes(JUDGMENT))
    assert res.documents[0]["outcome"] == R.WAIT_TEXT and res.people == [] and res.judgments[0]["citation"] == "[2099] NZSC 7"


def test_the_old_listing_s_judgments_the_corpus_lacks_are_catch_log_lines_not_rows():
    entries = [{"sha256": SHA, "source": "courtsofnz.govt.nz", "ref": "court:2099 NZSC 7", "url": "https://x/2099-NZSC-7.pdf"},
               {"sha256": SHA2, "source": "courtsofnz.govt.nz", "ref": "court:2099 NZSC 8", "url": "https://x/2099-NZSC-8.pdf"},
               {"sha256": SHA3, "source": "waitangitribunal.govt.nz", "ref": "waitangi:1", "url": "https://y/1.pdf"}]
    recs = [{"capture": SHA, "url": "https://z/other"}]
    gap = C.old_listing_gap(entries, recs)
    assert [(s, st) for s, st, _ in gap] == [(SHA2, "listing")] and "court:2099 NZSC 8" in gap[0][2]


def test_the_lane_opens_no_connection_to_a_court_site():
    for name in os.listdir(HERE):
        if name.endswith(".py"):
            src = open(os.path.join(HERE, name), encoding="utf-8").read()
            assert not re.search(r"\bfetchgate\b|urllib\.request|requests\.get|http\.client|feedparser", src), name
    spec = open(os.path.join(HERE, "spec.md"), encoding="utf-8").read()
    assert not hasattr(C, "fetch") and not hasattr(C, "case_links") and "qv4-courts-capture` (proposed" not in spec and "retired (ruling 127)" in spec


def test_mutants_of_the_recognition_are_caught(monkeypatch):
    e = {"url": "x.pdf"}
    pdf = b"%PDF"
    # a recogniser that trusted the MCP's kind would call a press summary a judgment
    monkeypatch.setattr(R, "PRESS", re.compile(r"NEVER MATCHES"))
    assert R.recognise(e, pdf, _texts(RELEASE))[0] != "courts-media-release"
    monkeypatch.undo()
    # one that read the court line only at the end of a line misses older files with the case number beside it
    old = JUDGMENT.replace("IN THE SUPREME COURT OF NEW ZEALAND", "IN THE SUPREME COURT OF NEW ZEALAND" + " " * 20 + "SC CIV 7/2004")
    assert R.recognise(e, pdf, _texts(old))[0] == "courts-nzsc-judgment"
    # one that let a judgment heading pass as submissions
    assert R.recognise(e, pdf, _texts(JUDGMENT.replace("[1]  The first paragraph.", "SUBMISSIONS were heard.")))[0] == "courts-nzsc-judgment"
