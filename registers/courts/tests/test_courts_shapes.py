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
from registers.courts import pieces as PC
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
# the kinds of 30 and 31 October 2026 (fix-2): shaped like the landed files, every name invented
ERA = page("IN THE EMPLOYMENT RELATIONS AUTHORITY", "AUCKLAND", "I TE RATONGA AHUMANA TAIMAHI", "TĀMAKI MAKAURAU ROHE", " " * 60 + "[2099] NZERA 123",
           " " * 66 + "3099123", L + "BETWEEN" + " " * 22 + "SAMPLE PERSON", N + "Applicant", L + "AND" + " " * 26 + "EXAMPLE HOLDINGS LIMITED",
           N + "Respondent", "Member of Authority:    A Member", "Representatives:        P Q Rowe, advocate for the applicant",
           "                        S T Vale, counsel for the respondent", "Investigation Meeting:  1 June 2099 at Auckland",
           "Submissions received:   8 June 2099 from the applicant", "Determination:          25 June 2099",
           "            DETERMINATION OF THE AUTHORITY", "Employment relationship problem", "[1]  The applicant raised a personal grievance.",
           "[2]  Non-publication order: an order prohibiting publication of the names of the parties is made.")
HRRT = page("IN THE HUMAN RIGHTS REVIEW TRIBUNAL" + " " * 30 + "[2099] NZHRRT 39", " " * 60 + "Reference No. HRRT 012/2098",
            L + "UNDER" + " " * 24 + "THE PRIVACY ACT 2020", L + "BETWEEN" + " " * 22 + "SAMPLE PERSON", N + "PLAINTIFF",
            L + "AND" + " " * 26 + "AN AGENCY", N + "DEFENDANT", "AT AUCKLAND", "BEFORE:", "A Chairperson", "A Member", "B Member",
            "REPRESENTATION:", "Sample Person in person", "P Q Rowe for defendant", "DATE OF HEARING: 1 June 2099", "DATE OF DECISION: 25 June 2099",
            "                 DECISION OF TRIBUNAL", "[1]  The plaintiff complained of an interference with privacy.", "[2]  Second.")
LCDT = page("NEW ZEALAND LAWYERS AND CONVEYANCERS DISCIPLINARY TRIBUNAL", " " * 60 + "[2099] NZLCDT 12", " " * 66 + "LCDT 004/99",
            L + "IN THE MATTER" + " " * 10 + "OF THE LAWYERS AND CONVEYANCERS ACT 2006", L + "BETWEEN" + " " * 22 + "A STANDARDS COMMITTEE",
            N + "Applicant", L + "AND" + " " * 26 + "SAMPLE PERSON", N + "Respondent", "CHAIR", "Judge Able", "MEMBERS OF TRIBUNAL", "Mr Baker", "Ms Carter",
            "HEARING at Auckland", "DATE OF HEARING 1 June 2099", "DATE OF DECISION 25 June 2099", "COUNSEL", "Mr Rowe for the Standards Committee",
            "            DECISION OF TRIBUNAL ON PENALTY", "[1]  The practitioner admitted the charge.", "[2]  Second.")
SSAA = page("[2099] NZSSAA 7", " " * 60 + "Reference No. SSA 012/99", L + "IN THE MATTER" + " " * 10 + "of the Social Security Act 2018",
            L + "AND", L + "IN THE MATTER" + " " * 10 + "of an appeal by XXXX of Auckland against a decision of a Benefits Review Committee",
            "BEFORE THE SOCIAL SECURITY APPEAL AUTHORITY", "Ms A Able - Chairperson", "Mr B Baker - Member", "Hearing at Auckland on 1 June 2099",
            "Appearances", "The appellant in person", "Ms Carter for the Chief Executive of the Ministry", "                 DECISION",
            "[1]  The appellant appeals a decision.", "[2]  Second.")
NZDC = page("IN THE DISTRICT COURT", "AT WELLINGTON", " " * 60 + "[2099] NZACC 45", " " * 60 + "ACR 12/99", L + "UNDER" + " " * 24 + "THE ACCIDENT COMPENSATION ACT 2001",
            L + "IN THE MATTER OF" + " " * 12 + "AN APPEAL UNDER SECTION 149 OF THE ACT", L + "BETWEEN" + " " * 22 + "SAMPLE PERSON", N + "Appellant",
            L + "AND" + " " * 26 + "ACCIDENT COMPENSATION CORPORATION", N + "Respondent", "Hearing:        1 June 2099", "Held at:        Wellington",
            "Appearances:    Mr Rowe for the Appellant", "                Ms Vale for the Respondent", "Judgment:       25 June 2099",
            "              JUDGMENT OF JUDGE ABLE", "[1]  The appellant appeals a review decision.", "[2]  Second.")
#: a hearing transcript under a judgment-like cover sheet (case-information files of 2008–2018): the case number beside the
#: court line, Appearances, no citation, no heading, the speakers from page 2
TRANSCRIPT_COVER = page("IN THE SUPREME COURT OF NEW ZEALAND" + " " * 20 + "SC 12/2099", L + "BETWEEN" + " " * 22 + "EXAMPLE HOLDINGS LIMITED",
                        N + "Appellant", L + "AND" + " " * 26 + "SAMPLE PERSON", N + "Respondent", "Hearing:       13 June 2099",
                        "Coram:         Able CJ", "               Baker J", "Appearances:   P Q Rowe KC for the Appellant", "               S T Vale for the Respondent",
                        "                 CIVIL APPEAL")
TRANSCRIPT_BODY = page("MR ROWE KC:", "May it please the Court.", "ABLE CJ:", "Yes Mr Rowe.", "MR ROWE KC:", "The appeal concerns a deposit.",
                       "WILLIAM BAKER J:", "Which clause?", "MR ROWE KC:", "Clause 4.")
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


def test_the_kinds_of_30_and_31_october_are_recognised_by_their_own_shapes():
    """The Employment Relations Authority's determinations (version 1 of the recogniser took 289 of 292 for counsel's
    submissions, by their 'Submissions received' label), the Human Rights Review Tribunal's decisions (275 set aside, 110
    submissions), the other tribunals (courts-judgment or submissions), the District Court (courts-judgment), and the 17
    hearing transcripts under a cover sheet filed as Supreme Court judgments."""
    e = {"url": "https://determinations.era.govt.nz/assets/elawpdf/2099/opaque.pdf", "kind": "judgment_pdf"}
    pdf = b"%PDF-1.4 fake"
    assert R.recognise(e, pdf, _texts(ERA)) == (R.ERA, "the Authority's court line with its citation, its DETERMINATION heading or its labels")
    assert R.recognise(e, pdf, _texts(HRRT))[0] == R.HRRT
    assert R.recognise(e, pdf, _texts(LCDT))[0] == R.TRIBUNAL
    assert R.recognise(e, pdf, _texts(SSAA))[0] == R.TRIBUNAL
    assert R.recognise(e, pdf, _texts(NZDC))[0] == R.NZDC
    assert R.recognise(e, pdf, _texts(JUDGMENT))[0] == "courts-nzsc-judgment", "the senior courts as before"
    assert R.recognise(e, pdf, _texts(EMPC))[0] == "courts-judgment", "the Employment Court keeps the generic profile"
    assert R.recognise(e, pdf, _texts(SUBMISSION))[0] == "courts-counsel-submission", "real submissions are still submissions"
    # the cover sheet alone, two pages, could be a short judgment: it is a transcript when the document is long, or speaks early
    cover_only = {1: TRANSCRIPT_COVER, 2: "A second page with no speakers."}
    assert R.recognise(e, pdf, cover_only)[0] == "courts-nzsc-judgment"
    long = {1: TRANSCRIPT_COVER, 2: "Index.", **{p: "Page %d of argument with no speaker labels." % p for p in range(3, 22)},
            **{p: TRANSCRIPT_BODY for p in range(22, 26)}}
    assert R.recognise(e, pdf, long) == (R.TRANSCRIPT, "a cover sheet with the case number beside the court line, Appearances, no judgment heading or citation, and speakers' lines: a hearing transcript")
    speaking = {1: TRANSCRIPT_COVER, 2: "Index.", 3: TRANSCRIPT_BODY}
    assert R.recognise(e, pdf, speaking)[0] == R.TRANSCRIPT
    silent = {1: TRANSCRIPT_COVER, **{p: "Page %d of a long judgment whose heading sits on page 3." % p for p in range(2, 30)}}
    assert R.recognise(e, pdf, silent)[0] == "courts-nzsc-judgment", "no speaker anywhere: a judgment with a long caption (two Court of Appeal files)"
    # mutants: a recogniser trusting the labels alone would still take a determination for submissions
    assert R.recognise(e, pdf, _texts(ERA.replace("[2099] NZERA 123", "").replace("DETERMINATION OF THE AUTHORITY", "")))[0] == R.ERA, "the labels carry it"
    assert R.recognise(e, pdf, _texts(ERA.replace("IN THE EMPLOYMENT RELATIONS AUTHORITY", "IN THE EMPLOYMENT COURT OF NEW ZEALAND")))[0] != R.ERA
    assert R.recognise(e, pdf, _texts(LCDT.replace("[2099] NZLCDT 12", "[2099] NZHC 12")))[0] != R.TRIBUNAL, "a court's citation code is no tribunal's"
    assert R.KIND_OF[R.ERA] == "determination" and R.KIND_OF[R.HRRT] == R.KIND_OF[R.TRIBUNAL] == "tribunal decision" and R.KIND_OF[R.NZDC] == "judgment"
    assert {R.ERA, R.HRRT, R.TRIBUNAL, R.NZDC} <= R.JUDGMENT_SLUGS, "each is read by the caption grammar and the text reader"


def test_the_caption_grammar_reads_the_new_kinds_and_their_non_publication_orders():
    from registers.courts import caption
    j = caption.parse({1: ERA}, "opaque.pdf")
    assert (j.citation, j.court, j.court_name, j.heading) == ("[2099] NZERA 123", "NZERA", "EMPLOYMENT RELATIONS AUTHORITY", "DETERMINATION")
    assert j.judgment_date.isoformat() == "2099-06-25" and j.date_basis == "label" and j.judges == "A Member"
    assert [(p.role, p.name) for p in j.parties] == [("Applicant", "SAMPLE PERSON"), ("Respondent", "EXAMPLE HOLDINGS LIMITED")]
    assert j.suppression and "order in the text" in j.suppression_kinds and j.status == "parsed", (j.status, j.missing, j.notes)
    assert [n for n, _ in j.paragraphs] == [1, 2]
    j = caption.parse({1: HRRT}, "2099-nzhrrt-39-x.pdf")
    assert (j.citation, j.court, j.court_name, j.heading) == ("[2099] NZHRRT 39", "NZHRRT", "HUMAN RIGHTS REVIEW TRIBUNAL", "DECISION")
    assert j.judgment_date.isoformat() == "2099-06-25" and j.judges.startswith("A Chairperson")
    assert [(p.role, p.name) for p in j.parties] == [("PLAINTIFF", "SAMPLE PERSON"), ("DEFENDANT", "AN AGENCY")], j.unrecognised   # roles as printed
    assert not j.suppression and j.status == "parsed", (j.status, j.missing)
    j = caption.parse({1: NZDC}, "2099-nzacc-45-x.pdf")
    assert (j.citation, j.court, j.court_name) == ("[2099] NZACC 45", "NZACC", "DISTRICT COURT") and j.judgment_date.isoformat() == "2099-06-25"
    assert [(p.role, p.name) for p in j.parties] == [("Appellant", "SAMPLE PERSON"), ("Respondent", "ACCIDENT COMPENSATION CORPORATION")]
    j = caption.parse({1: LCDT}, "x.pdf")
    assert (j.citation, j.court) == ("[2099] NZLCDT 12", "NZLCDT") and j.court_name is None, "IN THE MATTER OF … is a subject, not a court line"
    assert j.judgment_date.isoformat() == "2099-06-25", "DATE OF DECISION with no colon"
    assert caption.parse({1: HRRT.replace("DATE OF DECISION: 25 June 2099", "DATE OF MINUTE: 26 June 2099")}).judgment_date.isoformat() == "2099-06-26"
    assert caption._dated_line("DATE OF HEARING: 1 June 2099\nDATE OF LAST SUBMISSIONS: 2 June 2099") is None
    # the wording the Authority and the tribunals use for an order
    for words in ("A non-publication order is made.", "the order for non-publication stands", "the names of the parties are anonymised"):
        assert caption.BODY_SUPPRESS.search(words), words
    assert not caption.BODY_SUPPRESS.search("the publication was anonymised by the newspaper"), "anonymised alone is not an order"
    assert caption.court_line("IN THE MATTER OF THE LAWYERS AND CONVEYANCERS DISCIPLINARY TRIBUNAL") is None
    assert caption.court_line("IN THE COURT OF APPEAL OF NEW ZEALAND").group(1) == "COURT OF APPEAL"
    assert caption.court_line("IN THE DISTRICT COURT AT WELLINGTON").group(1) == "DISTRICT COURT"
    assert caption.court_line("IN THE WEATHERTIGHT HOMES TRIBUNAL").group(1) == "WEATHERTIGHT HOMES TRIBUNAL"


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
    assert not hasattr(M, "excerpt"), "the reader never excerpts: a long document is read in pieces by its profile's rule (ruling 130)"


def _fake_store(tmp, docs: dict):
    """A reader store holding one text reader's reading per document, as read_one would store it."""
    store = rd.Store(tmp)
    for sha, (slug, answer) in docs.items():
        version = R.profile_version(slug)
        store.put(rd.Reading(sha, 1, M.READER, M.TEXT_MODEL, M.settings(PC.rule_of(slug)), slug, version, "text",
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
    assert doc[SHA]["pieces"] == doc[SHA2]["pieces"] == doc[SHA3]["pieces"] == 1 and doc[SHA3]["text_chars"] < 2000, "a case page's text is the model's, not its HTML"
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


def test_a_file_under_several_records_is_read_once_and_every_record_s_row_carries_the_reading(monkeypatch):
    """The corpus holds the same bytes under more than one record (the merge
    gate of 30 October: a case page with and without `?searchterm=None`, a
    judgment under two file names), and every row keyed by the file's hash
    is emitted once; each record is still its own documents row."""
    pages = {SHA: {1: JUDGMENT}, SHA2: {1: RELEASE}}
    monkeypatch.setattr(R, "_texts_of", lambda data, sha, store, v: (pages[sha], "text", []))
    monkeypatch.setattr(R, "page_total", lambda data: 1)
    import support.docread.read as DR
    monkeypatch.setattr(DR, "read_document", lambda *a, **k: None)
    u1, u2, u3, u4 = _entries()
    entries = [{**u3, "record_id": "u3b", "record": "6" * 64, "seq": 5, "url": URL + "/?searchterm=None"},   # listed first on purpose
               u1, u2, u3, {**u1, "record_id": "u1b", "record": "7" * 64, "seq": 6, "url": u1["url"].replace(".pdf", "_000.pdf")},
               u4, {**u4, "record_id": "u4b", "record": "8" * 64, "seq": 7, "url": u4["url"].replace(".pdf", "_000.pdf")}]
    data = {SHA: _pdf_bytes(JUDGMENT), SHA2: _pdf_bytes(RELEASE), SHA3: CASE_PAGE.encode()}
    people = [{"name": "Sample Person", "kind": "person", "role": "party", "role_text": "respondent", "for": None}]
    with tempfile.TemporaryDirectory() as td:
        store = _fake_store(td, {SHA: ("courts-nzsc-judgment", {"summary": "A judgment.", "people": people})})
        res = R.read(entries, [], store=store, data_of=lambda sha: data.get(sha))
    assert len(res.cases) == 1 and len(res.judgments) == 1 and len(res.parties) == 2 and len(res.people) == 1
    assert res.counts["records"] == 7 and res.counts["shared"] == 3 and res.counts["read"] == 2 and res.counts["caught"] == 2
    assert len(res.case_links) == res.cases[0]["links"] and len(res.paragraphs) == 2
    assert res.cases[0]["url"] == URL, "the plain url is the one read, whichever the pull listed first"
    assert res.judgments[0]["source_url"].endswith("/2099-NZSC-7.pdf")
    for name in ("documents", "cases", "case_links", "judgments", "parties", "people"):
        keys = [r["key"] for r in getattr(res, name)]
        assert len(keys) == len(set(keys)), name
    docs = {d["key"]: d for d in res.documents}
    assert len(docs) == 7
    for a, b in (("u3", "u3b"), ("u1", "u1b"), ("u4", "u4b")):
        assert docs[a]["document"] == docs[b]["document"] and docs[a]["url"] != docs[b]["url"]
        assert all(docs[a][k] == docs[b][k] for k in R.SHARED_READING), (a, b)
    assert docs["u1"]["outcome"] == "read" and docs["u1b"]["summary"] == "A judgment."
    assert docs["u3"]["outcome"] == R.WAIT_TEXT and docs["u4b"]["outcome"] == "caught"
    lines = {(item, stage) for item, stage, _ in res.set_aside}
    assert ("u4", "pull") in lines and ("u4b", "pull") in lines, "a caught file is a catch-log line for each record"
    assert not any(item in ("u1b", "u3b") for item, _, _ in res.set_aside), "a read file is no line"


def test_a_document_its_rule_cannot_split_is_set_aside_at_read_and_never_waits_on_the_text_reader(monkeypatch):
    long_release = {1: RELEASE, 2: "A very long annex. " * 2000}          # 38,000 characters under the whole rule
    pages = {SHA: {1: JUDGMENT}, SHA2: long_release}
    monkeypatch.setattr(R, "_texts_of", lambda data, sha, store, v: (pages[sha], "text", []))
    monkeypatch.setattr(R, "page_total", lambda data: 2)
    import support.docread.read as DR
    monkeypatch.setattr(DR, "read_document", lambda *a, **k: None)
    data = {SHA: _pdf_bytes(JUDGMENT), SHA2: _pdf_bytes(RELEASE)}
    with tempfile.TemporaryDirectory() as td:
        res = R.read(_entries()[:2], [], store=rd.Store(td), data_of=lambda sha: data.get(sha))
    docs = {d["document"]: d for d in res.documents}
    assert docs[SHA]["outcome"] == R.WAIT_TEXT and docs[SHA]["pieces"] == 1
    assert docs[SHA2]["outcome"] == "set aside" and docs[SHA2]["pieces"] is None and docs[SHA2]["profile"] == "courts-media-release"
    assert docs[SHA2]["citation"] == "[2099] NZSC 7", "the sheet's facts are still read"
    lines = [(item, stage, reason) for item, stage, reason in res.set_aside if item == "u2"]
    assert len(lines) == 1 and lines[0][1] == "read" and lines[0][2].startswith("the text reader cannot read it:") and "whole" in lines[0][2]
    assert res.counts["set aside"] == 1 and res.counts[R.WAIT_TEXT] == 1


def test_a_long_judgment_waits_with_its_piece_count(monkeypatch):
    from registers.courts.tests.test_courts_pieces import _judgment
    texts = _judgment(150)
    monkeypatch.setattr(R, "_texts_of", lambda data, sha, store, v: (texts, "text", []))
    monkeypatch.setattr(R, "page_total", lambda data: len(texts))
    import support.docread.read as DR
    monkeypatch.setattr(DR, "read_document", lambda *a, **k: None)
    with tempfile.TemporaryDirectory() as td:
        res = R.read(_entries()[:1], [], store=rd.Store(td), data_of=lambda sha: _pdf_bytes("x"))
    d = res.documents[0]
    assert d["outcome"] == R.WAIT_TEXT and d["pieces"] >= 4 and d["pieces"] == PC.count(texts, PC.rule_of("courts-nzsc-judgment"))
    assert res.judgments[0]["paragraphs"] == 150


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
