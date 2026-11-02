"""The minutes' reading (profiles council-minutes-standard and council-minutes-text v1), on invented minutes and a fake
text reader: recognition both ways (the standard template, any other minutes, a scan, a page that is no minutes); the
two skips (a public-excluded part to the readmission or the end, an item that names public-excluded minutes, a public
forum item) run before anything is read and the text reader never sees what they skip; the standard template's
attendance, apologies, declarations and resolutions; the address flag; the text reader's answer kept only where the
lane keeps it, stored once per piece and replayed; the load's ledger and rows. Every name, council and place is
invented. No model, no database, no PDF."""
import json
import tempfile

import pytest

from support import reader as rd
from registers.council_minutes import load, minutes as M, model_read as MR

SHA = "a1" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"

STANDARD = {1: """INVENTED DISTRICT COUNCIL
Minutes of a meeting of the Invented District Council held on 22 October 2026 at 9.30 am

PRESENT:            His Worship the Mayor T Pretend (Chairperson), Cr A Example, Cr B Sample,
                    Deputy Mayor C Madeup and Cr D Notreal

IN ATTENDANCE:      E Placeholder (Chief Executive), F Fictional (Group Manager - Planning)

1            KARAKIA

2            APOLOGIES

RESOLUTION 2026/1
Moved:           Cr Example
Seconded:        Cr Sample
That the apology received from Cr Gloria Absent be accepted.
                                                                                        CARRIED

3            PUBLIC FORUM
             Hemi Speaker spoke about the Invented Road footpath.
RESOLUTION 2026/2
Moved:           Cr Example
Seconded:        Cr Sample
That the public forum presentation be received.
                                                                                        CARRIED
""", 2: """4            DECLARATIONS OF INTEREST
             Cr B Sample declared an interest in item 6.1 and left the room.

6            REPORTS

6.1          SALE OF LAND AT 14 PRETEND STREET
RESOLUTION 2026/3
Moved:           Deputy Mayor Madeup
Seconded:        Cr Notreal
That the Council approves the sale of the land at 14 Pretend Street, Nowhere.
For:             Crs Example, Madeup and Notreal
Against:         Cr Pretend
                                                                                        CARRIED

6.2          ANNUAL PLAN
RESOLUTION 2026/4
Moved:           Cr Notreal
Seconded:        Cr Example
That the report be received.
                                                                                        LOST

7            RESOLUTION TO EXCLUDE THE PUBLIC
RESOLUTION 2026/5
Moved:           Cr Example
Seconded:        Cr Sample
That the public be excluded from the following part of the meeting: item 8.1 Secret Person's Employment.
                                                                                        CARRIED
8.1          SECRET PERSON EMPLOYMENT
RESOLUTION 2026/6
Moved:           Cr Example
Seconded:        Cr Sample
That Secret Person be paid.
                                                                                        CARRIED
The public were re-admitted at 11.05 am.

9            CLOSING KARAKIA
RESOLUTION 2026/7
Moved:           Cr Sample
Seconded:        Cr Example
That the meeting be closed.
                                                                                        CARRIED
"""}

OTHER = {1: """Invented Regional Council
Minutes of the Invented Regional Council meeting held on 22 October 2026

Present:   Chair Tia Pretend, Cr Ana Example, Cr Ben Sample
In Attendance:   Cara Fictional (Chief Executive)

3. Apologies
   That the Council accepts the apology from Cr Dan Notreal.
                                                          Carried
Public Excluded
   That Secret Person be paid.
""", 2: "4.1 Report\n Resolved: That the report be received. Example/Sample  Carried\n"}


@pytest.fixture
def pdf(monkeypatch):
    """A PDF whose text layer is `texts`, without a PDF: the text-layer helpers stand in."""
    from support.docread import pages
    state = {"texts": STANDARD, "how": "text"}
    monkeypatch.setattr(pages, "text_pages", lambda data, *a, **k: dict(state["texts"]))
    monkeypatch.setattr(pages, "read_from", lambda data, texts=None: state["how"])
    monkeypatch.setattr(pages, "thin_pages", lambda texts: [p for p, t in texts.items() if len((t or "").strip()) < 20])
    return state


def test_the_profiles_are_proposed():
    from support import profiles
    for slug in (M.STANDARD, M.TEXT):
        p = profiles.profile(slug, path=MR.PROPOSED)
        assert p and p["version"] >= 1 and p["role"] == "read", slug
    assert profiles.profile(M.TEXT, path=MR.PROPOSED)["reading"]["budget_chars"] == MR.BUDGET_CHARS


def test_recognition_both_ways():
    assert M.recognise(STANDARD, "text") == (M.STANDARD, "")
    assert M.recognise(OTHER, "text") == (M.TEXT, "")
    assert M.recognise(STANDARD, "pixels") == ("", M.WAIT_PAGES)
    assert M.recognise({1: "Agenda of the Invented Council. Items to be discussed. " * 5}, "text") == ("", M.NOT_MINUTES)


def test_the_two_skips_take_the_public_excluded_part_and_the_public_forum_item():
    kept, skipped = M.sections(STANDARD)
    text = "\n".join(l for _p, l in kept)
    assert "Secret Person" not in text and "Hemi Speaker" not in text and "public forum presentation" not in text
    assert "That the meeting be closed." in text, "the readmission ends the public-excluded part"
    assert skipped["public excluded parts"] == 1 and skipped["public forum items"] == 1
    kept2, sk2 = M.sections(OTHER)
    assert "Secret Person" not in "\n".join(l for _p, l in kept2) and sk2["public excluded parts"] == 1, \
        "a banner with no readmission excludes to the end"
    _k, sk3 = M.sections({1: "5      CONFIRMATION OF PUBLIC EXCLUDED MINUTES\n  That they be confirmed.\n"
                             "6      REPORTS\n  kept line\n"})
    assert sk3["public excluded parts"] == 1 and "kept line" in "\n".join(l for _p, l in _k)


def test_the_standard_template_reads_attendance_declarations_and_resolutions():
    got = M.read_standard(STANDARD)
    present = [(a["name"], a["role"]) for a in got["attendance"] if a["attendance"] == "present"]
    assert present == [("T Pretend", "Mayor, Chairperson"), ("A Example", "Councillor"), ("B Sample", "Councillor"),
                       ("C Madeup", "Deputy Mayor"), ("D Notreal", "Councillor")]
    officers = [(a["name"], a["title"]) for a in got["attendance"] if a["attendance"] == "in attendance"]
    assert officers == [("E Placeholder", "Chief Executive"), ("F Fictional", "Group Manager - Planning")]
    assert [a["name"] for a in got["attendance"] if a["attendance"] == "apology"] == ["Gloria Absent"]
    assert [(d["member"], d["item"]) for d in got["declarations"]] == [("B Sample", "6.1")]
    res = got["resolutions"]
    assert [r["number"] for r in res] == ["2026/1", "2026/3", "2026/4", "2026/7"], "nothing of the forum or the excluded part"
    r3 = res[1]
    assert (r3["item"], r3["item_title"], r3["mover"], r3["seconder"], r3["outcome"]) == (
        "6.1", "SALE OF LAND AT 14 PRETEND STREET", "Deputy Mayor Madeup", "Cr Notreal", "CARRIED")
    assert r3["votes_for"] == "Crs Example, Madeup and Notreal" and r3["votes_against"] == "Cr Pretend"
    assert r3["text"] == "That the Council approves the sale of the land at 14 Pretend Street, Nowhere."
    assert res[2]["outcome"] == "LOST" and M.names_address(r3["text"]) and not M.names_address(res[2]["text"])


def test_an_attendee_is_one_named_person():
    assert M.attendee("members of the public", "present") is None
    assert M.attendee("Invented Regional Council", "in attendance") is None
    assert M.attendee("3 members of the media", "present") is None
    assert M.attendee("Cr Jo Bloggs (via Zoom)", "present") is None
    a = M.attendee("Kim Invented – Chief Executive", "in attendance")
    assert (a["name"], a["title"]) == ("Kim Invented", "Chief Executive")


def test_a_list_printed_one_person_a_line_and_a_heading_form_label():
    lines = M.lines_of({1: "2       PRESENT - NGĀ MANUKURA\n\nMayor Ana Pretend, Cr Ben Example and Cr Cy Sample.\n\n"
                           "ELECTED MEMBERS IN ATTENDANCE\n\nChair Di Notreal\nCr Ed Madeup\n\n3       APOLOGIES\n"})
    got = M.attendance(lines)
    assert [(a["name"], a["attendance"]) for a in got] == [
        ("Ana Pretend", "present"), ("Ben Example", "present"), ("Cy Sample", "present"),
        ("Di Notreal", "in attendance"), ("Ed Madeup", "in attendance")]


# ── the text reader's side ──────────────────────────────────────────────────────────────────────────────────────
ANSWER = json.dumps({"attendance": [
    {"name": "Tia Pretend", "role": "Chair", "title": None, "attendance": "present"},
    {"name": "Cara Fictional", "role": None, "title": "Chief Executive", "attendance": "in attendance"},
    {"name": "A member of the public", "role": None, "title": None, "attendance": "present"},
    {"name": "14 Pretend Street", "role": None, "title": None, "attendance": "present"},
    {"name": "Dan Notreal", "role": "Cr", "title": None, "attendance": "apology"},
    {"name": "Odd", "attendance": "somewhere"}],
    "declarations": [{"member": "Ben Sample", "item": "4.1", "text": "Cr Sample declared an interest in item 4.1."}],
    "resolutions": [{"item": "4.1", "item_title": "Report", "number": None, "mover": "Example", "seconder": "Sample",
                     "text": "That the report be received.", "outcome": "carried"},
                    {"item": None, "text": ""}]})


def _server(answers, calls: list):
    answers = list(answers)

    def post(url, body, timeout):
        calls.append(body)
        a = answers.pop(0) if len(answers) > 1 else answers[0]
        return {"model": body["model"], "choices": [{"message": {"content": a}}], "usage": {}}
    return post


def test_the_answer_is_kept_only_where_the_lane_keeps_it():
    got = MR.parse_answer("Here: " + ANSWER)
    assert [(a["name"], a["attendance"]) for a in got["attendance"]] == [
        ("Tia Pretend", "present"), ("Cara Fictional", "in attendance"), ("Dan Notreal", "apology")]
    assert [r["outcome"] for r in got["resolutions"]] == ["CARRIED"] and got["declarations"][0]["item"] == "4.1"
    assert MR.parse_answer("no json") is None


def test_the_text_reader_never_sees_a_skipped_part_and_reads_once(pdf):
    pdf["texts"] = OTHER
    calls = []
    store = rd.Store(tempfile.mkdtemp())
    got = MR.read_document(SHA, b"%PDF-1.7", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
    assert got["state"] == "read" and got["read"] == got["pieces"] == 1 and got["resolutions"] == 1
    sent = calls[0]["messages"][1]["content"]
    assert "Secret Person" not in sent and "Cara Fictional" in sent
    again = MR.read_document(SHA, b"%PDF-1.7", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
    assert again["replayed"] == 1 and again["read"] == 0 and len(calls) == 1, "a stored piece is never asked again"
    back = MR.replay(SHA, b"%PDF-1.7", version=1, store=store)
    assert back["state"] == "read" and [a["name"] for a in back["attendance"]] == ["Tia Pretend", "Cara Fictional", "Dan Notreal"]
    assert back["skipped"]["public excluded parts"] == 1
    empty = MR.replay("b2" * 32, b"%PDF-1.7", version=1, store=store)
    assert empty["state"] == MR.WAIT_TEXT, "a piece not yet read makes the document wait"
    pdf["texts"] = STANDARD
    assert MR.read_document(SHA, b"%PDF-1.7", version=1, store=store)["state"].startswith("the council-minutes-standard")


def test_the_load_reads_each_landed_minutes_pdf_into_the_ledger_and_its_rows(pdf, monkeypatch):
    monkeypatch.setattr(load, "standard_version", lambda: 1)
    meetings = {"invented.infocouncil.biz/CO_20261022_AGN": {
        "key": "invented.infocouncil.biz/CO_20261022_AGN", "council": "Invented District Council", "body": "Council",
        "meeting_date": "2026-10-22", "minutes_sha256": SHA, "minutes_held": "landed"}}
    captured = {"https://invented/1.PDF": ("landed", SHA), "https://invented/2.PDF": ("landed", "b2" * 32),
                "https://invented/3.PDF": ("held by the old estate", "c3" * 32)}
    blobs = {SHA: b"%PDF-1.7 standard", "b2" * 32: b"<html>not a pdf</html>"}
    out = load.read_minutes(meetings, captured, read_bytes=lambda s: blobs[s], store=rd.Store(tempfile.mkdtemp()))
    ledger = {r["document"]: r for r in out["minutes_read"]}
    assert set(ledger) == {SHA, "b2" * 32}, "every landed minutes PDF has a ledger line; the old estate's are not read"
    assert ledger[SHA]["state"] == "read" and ledger[SHA]["resolutions"] == 4 and ledger[SHA]["excluded_parts"] == 1
    assert ledger["b2" * 32]["state"] == "set aside: not a PDF"
    r = [x for x in out["resolutions"] if x["number"] == "2026/3"][0]
    assert r["text_names_address"] and r["document"] == SHA and r["page"] == 2 and r["meeting_key"].endswith("_AGN")
    assert all(x["key"].startswith(SHA + "/") for t in ("attendance", "resolutions", "declarations") for x in out[t])


def test_a_running_head_is_dropped_but_never_a_line_a_skip_turns_on():
    head = "Minutes of the Sample District Council {} October 2026"
    words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliet", "kilo", "lima"]
    texts = {p: "\n".join(["CONFIRMED", head.format(p), "PUBLIC EXCLUDED"]
                          + [f"{w} {words[(i + p) % 12]}" for i, w in enumerate(words)] + ["CARRIED", f"Page {p}"])
             for p in range(1, 5)}
    kept = [l for _p, l in M.lines_of(texts)]
    assert "CONFIRMED" not in kept and not any(l.startswith("Minutes of the Sample") for l in kept)
    assert kept.count("PUBLIC EXCLUDED") == 4 and kept.count("CARRIED") == 4 and "alpha delta" in kept
    # a head must be on three pages: a two-page document keeps its lines
    assert "CONFIRMED" in [l for _p, l in M.lines_of({1: texts[1], 2: texts[2]})]


def test_a_resolution_with_no_text_is_counted_not_kept():
    text = ("PRESENT\nCr A Sample, Cr B Sample\n"
            "6.2  FUNDING APPLICATION\nRESOLUTION 2026/5\nMoved: Cr A Sample\nSeconded: Cr B Sample\n\n"
            "RESOLUTION 2026/6\nThat the board approve the sum of $10.\nMoved: Cr A Sample\nSeconded: Cr B Sample\nCARRIED\n")
    got = M.read_standard({1: text})
    assert [r["number"] for r in got["resolutions"]] == ["2026/6"]
    assert got["skipped"]["resolutions with no text"] == 1
