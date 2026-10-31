"""The ministers' diaries and Parliament's records as their lanes' pane.md
state them (registers/ministers_diaries, registers/parliament; rulings 78,
96, 101, 102): a release titled minister and month, citing the PDF or
saying "file name only: no address served", its meetings in date and time
order; a meeting shown whole as released with a small note where a flag
says it names an address, the release's withholding words as they stand,
pointing at its release and at no person; a written question titled as the
API gives it, its question and reply whole, cited by its hash and
Parliament's document id, joined to Hansard by Parliament's member id and
never by a name; an API item and an archived page with their text whole;
a withdrawn row struck, a row of several versions saying so. Every row says
the estate fetched nothing. The addresses here are made up."""
import datetime as dt

from products.board import catalogue as cat
from products.board import graph, panes, search
from products.board.tests.test_panes import ctx

PDF = "https://www.beehive.govt.nz/sites/default/files/2026-07/Hon%20Jane%20Doe%20-%20June%202026.pdf"
DIARY = {"document": "ab" * 32, "page": 1, "place": "record", "read_from": "text",
         "reader": "registers.ministers_diaries.read", "profile": "mcp-parliament-diaries-record",
         "source_note": "read from the release PDF by Arthur's provider off-estate (ruling 78)"}


def release(**kw):
    r = {"key": "Hon Jane Doe - June 2026.pdf", "citation_url": PDF, "file_name": "Hon Jane Doe - June 2026.pdf",
         "upload_folder": "2026-07", "minister": "Hon Jane Doe", "ministers_named": 1, "portfolios": ["Transport"],
         "month": "2026-06", "month_named": "2026-06", "entries_month": "2026-06", "months": 1,
         "first_on": dt.date(2026, 6, 1), "last_on": dt.date(2026, 6, 30), "entries": 79, "withheld_entries": 4,
         "locations_flagged": 1, **DIARY}
    r.update(kw)
    return r


def entry(**kw):
    r = {"key": "205056", "release": "Hon Jane Doe - June 2026.pdf", "citation_url": PDF,
         "file_name": "Hon Jane Doe - June 2026.pdf", "month": "2026-06", "rowid": 205056, "minister": "Hon Jane Doe",
         "portfolio": "Transport", "entry_on": dt.date(2026, 6, 23), "date_as_released": "2026-06-23",
         "time": "7:00 pm - 7:30 pm", "meeting": "Meeting with the Sample Trust", "attendees": "Withheld under s9(2)(a)",
         "location": "12 Sample Street, Sampletown", "location_names_home": False, "location_street_only": True,
         "meeting_names_address": False, "attendees_names_address": False, "withheld": ["attendees"],
         "collected_at": "2026-10-17T06:35:49Z", "updated_at": "2026-10-17T06:35:49Z", "versions": 1, **DIARY}
    r.update(kw)
    return r


PARL = {"document": "cd" * 32, "page": None, "place": "record", "read_from": "text", "reader": "registers.parliament.read",
        "profile": "mcp-parliament-written-questions-record",
        "source_note": "captured off-estate by Arthur's provider (ruling 78); the estate never fetched parliament.nz"}
MEMBER = "d6624385-7592-47d0-b13f-7f6b10a02610"


def question(**kw):
    r = {"key": "1782ae4e", "document_id": "WQ_41487_2026", "question_number": 41487, "question_year": 2026,
         "parliament_number": 54, "title": "41487 (2026). Jane Roe to the Minister for Sample Affairs",
         "member_id": MEMBER, "minister_name": "Hon Jane Doe", "ministerial_display_name": "Minister for Sample Affairs",
         "document_type": "WrittenQuestion", "question_released_at": "2026-09-24T00:00:00Z",
         "question_released_on": dt.date(2026, 9, 24), "dated": "2026-10-01", "last_modified": "2026-10-01T13:08:43Z",
         "reply_present": True, "question_text": "What is the cost of the works at 12 Sample Road?",
         "question_text_names_address": True, "reply_text": "I refer the member to my earlier reply.",
         "reply_text_names_address": False, "attachment_name": None, "provider_fetched_at": "2026-10-26T10:31:50+00:00",
         "capture": None, "served": True, "versions": 1, "citation_url": None, **PARL}
    r.update(kw)
    return r


SUBMIT = "https://www.parliament.nz/en/pb/sc/make-a-submission/document/54SCMAOC_SCF_X/sample-bill"


def item(**kw):
    r = {"key": "parliament-sc-submissions/54SCMAOC_SCF_X", "corpus": "parliament-sc-submissions",
         "record_id": "54SCMAOC_SCF_X", "document_type": "Submissions called for", "item_type": None,
         "title": "Sample Claims Settlement Bill", "short_title": None, "bill_title": None, "bill_number": None,
         "bill_current_stage_name": None, "bill_stages": [], "select_committee": None, "member_name": None,
         "party_name": None, "author": "Māori Affairs Committee", "people": None,
         "publication_date": "2026-09-24T00:00:00Z", "publication_on": dt.date(2026, 9, 24),
         "iob_closing_date": "2099-01-01T00:00:00Z", "parliament_number": 54, "status": "Open",
         "text": "Submissions are invited on the Sample Claims Settlement Bill.", "text_names_address": False,
         "capture": {"url": "/en/pb/sc/make-a-submission/document/54SCMAOC_SCF_X/sample-bill", "status": "Open"},
         "served": True, "versions": 1, "citation_url": SUBMIT, **PARL}
    r.update(kw)
    return r


OLD = "http://www.parliament.nz:80/en-NZ/SC/SubmCalled/b/3/4/b343.htm"
SNAP = "https://web.archive.org/web/20070516102214id_/" + OLD


def page(**kw):
    r = {"key": OLD, "citation_url": OLD, "snapshot_url": SNAP, "archived_at": "2007-05-16T10:22:14Z",
         "dated": "2007-05-16", "html_title": "Submissions called for", "doc_type": "other", "kind": None,
         "text": "The committee calls for submissions.", "text_names_address": False, "text_words": 263,
         "captured_at": "2026-10-22T20:20:44+00:00", "captured_sha256": "ef" * 32, "capture_status": "ok",
         "capture": {"kind": "doc", "snapshots": 1}, "served": True, "versions": 1, **PARL}
    r.update(kw)
    return r


def test_the_registers_sit_near_hansard_and_the_beehive_in_the_house_s_family():
    regs = [r for r, _ in cat.REGISTERS]
    assert regs.index("parliament") + 1 == regs.index("hansard")
    assert regs.index("ministers_diaries") == regs.index("beehive") + 1
    assert dict(cat.REGISTERS)["ministers_diaries"] == "Ministers' diaries: who met the minister"
    assert dict(cat.REGISTERS)["parliament"] == "Parliament: written questions, bills, papers and archived pages"
    for reg in ("parliament", "ministers_diaries"):
        assert cat.FAMILY_OF[reg] == "the House" and cat.REGISTER_COLOUR[reg] == cat.REGISTER_COLOUR["house"]
        assert reg not in dict(cat.NOT_HELD)
    assert cat.main_view_of("ministers_diaries") == "minister_diary_releases"
    assert cat.main_view_of("parliament") == "parliament_written_questions"
    assert [v.name for v in cat.views_of("parliament")] == ["parliament_written_questions", "parliament_api_items",
                                                            "parliament_wayback_pages", "parliament_people"]


def test_a_release_is_its_minister_and_month_citing_the_pdf_with_its_meetings_in_order():
    v = cat.BY_NAME["minister_diary_releases"]
    r = release()
    assert panes.title_of(v, r) == "Hon Jane Doe · 2026-06"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert f'href="{PDF}"' in html and "file name only" not in html and "ababababab" in html
    assert "79" in html and "did not fetch the PDF" in html and "person: the group" not in html
    [j] = v.joins
    assert (j.view, j.column, j.order) == ("minister_diary_entries", "release", "entry_on, rowid")


def test_a_release_with_no_address_says_so_and_makes_none_up():
    v = cat.BY_NAME["minister_diary_releases"]
    r = release(citation_url=None, month=None, file_name="26 October 2017 - 31 December 2018.pdf")
    assert panes.title_of(v, r) == "Hon Jane Doe · 26 October 2017 - 31 December 2018.pdf"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "file name only: no address served" in html and "beehive.govt.nz" not in html
    assert "file name only: no address served" in panes.hit("", v, r, [])


def test_a_meeting_is_shown_whole_with_its_flag_note_and_withholding_words_pointing_at_no_person():
    v = cat.BY_NAME["minister_diary_entries"]
    r = entry()
    assert panes.title_of(v, r) == "23 June 2026 · 7:00 pm - 7:30 pm · Meeting with the Sample Trust"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "12 Sample Street, Sampletown" in html            # whole, as released: the board is Arthur's instrument (ruling 102)
    assert "(street address, no place of business named)" in html and "(names a home)" not in html
    assert "Withheld under s9(2)(a)" in html and "did not fetch the PDF" in html
    assert "(names a home)" in panes.row_pane(ctx(v, entry(location_names_home=True), same_words=[]))
    flagged = entry(location_street_only=False, meeting_names_address=True, attendees_names_address=True)
    hit = panes.hit("", v, flagged, [])
    assert "(street address in the meeting)" in hit and "(street address in the attendees)" in hit
    assert cat.pointers(v) == {"release": ("minister_diary_releases", "key")}
    assert v.kind != "person" and v.names == () and v.relations == () and "person: the group" not in html
    assert "location" not in v.search


def test_the_diaries_draw_no_edge_and_name_the_minister_given_first():
    for name in ("minister_diary_releases", "minister_diary_entries"):
        v = cat.BY_NAME[name]
        assert v.relations == () and name not in graph.INCOMING
        assert [(n.whole, n.order) for n in cat.fields_of(v).names] == [("minister", cat.GIVEN_FAMILY)]


def test_a_meeting_of_several_versions_says_which_it_was_read_from():
    v = cat.BY_NAME["minister_diary_entries"]
    assert "read from the version taken last, of 3" in panes.row_pane(ctx(v, entry(versions=3), same_words=[]))


def test_a_release_s_meetings_are_asked_in_date_and_time_order():
    seen = []

    def rows(conn, sql, params):
        seen.append(sql)
        return []
    real = search.db.rows
    search.db.rows = rows
    try:
        search.children(object(), cat.BY_NAME["minister_diary_releases"], release())
    finally:
        search.db.rows = real
    assert "from pub.minister_diary_entries where release = %s order by entry_on, rowid" in seen[0]


def test_a_written_question_is_titled_as_served_its_texts_whole_cited_by_hash_and_document_id():
    v = cat.BY_NAME["parliament_written_questions"]
    r = question()
    assert panes.title_of(v, r) == "41487 (2026). Jane Roe to the Minister for Sample Affairs"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "What is the cost of the works at 12 Sample Road?" in html and "my earlier reply" in html
    q_head = html[html.index("The question, as the API gives it"):html.index("The reply, as the API gives it")]
    r_head = html[html.index("The reply, as the API gives it"):]
    assert "names an address by its shape" in q_head and "names an address by its shape" not in r_head[:300]
    assert "WQ_41487_2026" in html and "no page address: the API gives none" in html
    assert "41487" in html and "Hon Jane Doe" in html and "24 September 2026" in html
    assert "did not fetch parliament.nz" in html and "person: the group" not in html
    hit = panes.hit("", v, r, [])
    assert "12 Sample Road" not in hit and "WQ_41487_2026" in hit      # the texts are in the row pane alone


def test_a_written_question_joins_hansard_by_parliament_s_member_id_and_never_by_a_name():
    v = cat.BY_NAME["parliament_written_questions"]
    [rel] = v.relations
    assert (rel.column, rel.view, rel.to_column) == ("member_id", "hansard_speeches", "member_id")
    assert rel.kind in cat.RELATION_KINDS and cat.pointers(v) == {}
    assert (v, rel) in graph.INCOMING["hansard_speeches"]
    named = {c for vv in cat.VIEWS for n in cat.fields_of(vv).names for c in n.columns()}
    for name in ("parliament_written_questions", "parliament_api_items", "parliament_wayback_pages"):
        w = cat.BY_NAME[name]
        assert not {r.column for r in w.relations} & (named | {"minister_name", "member_name", "title"})
    assert cat.BY_NAME["parliament_api_items"].relations == () and cat.BY_NAME["parliament_wayback_pages"].relations == ()
    assert [(n.whole, n.order) for n in cat.fields_of(v).names] == [("minister_name", cat.GIVEN_FAMILY)]
    assert [(n.whole, n.order) for n in cat.fields_of(cat.BY_NAME["parliament_api_items"]).names] == [
        ("member_name", cat.GIVEN_FAMILY)]


def test_a_withdrawn_row_is_struck_and_several_versions_say_so():
    v = cat.BY_NAME["parliament_written_questions"]
    html = panes.row_pane(ctx(v, question(served=False, versions=2), same_words=[]))
    assert "<h2><s>" in html and "withdrawn by the source" in html
    assert "read from the version taken last, of 2" in html
    plain = panes.row_pane(ctx(v, question(), same_words=[]))
    assert "<s>" not in plain and "withdrawn by the source" not in plain and "version taken last" not in plain
    assert "<s>" in panes.hit("", v, question(served=False), [])
    assert "<s>" in panes.row_link("", [], v, question(served=False))


def test_an_api_item_shows_its_corpus_capture_and_text_and_cites_its_page():
    v = cat.BY_NAME["parliament_api_items"]
    r = item()
    assert panes.title_of(v, r) == "Sample Claims Settlement Bill · Submissions called for"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert f'href="{SUBMIT}"' in html and "parliament-sc-submissions" in html and "Māori Affairs Committee" in html
    assert "status: Open" in html and "Submissions are invited" in html and "names an address" not in html
    assert "no page address in the record" not in html
    bill = panes.row_pane(ctx(v, item(citation_url=None, corpus="parliament-bills", text_names_address=True), same_words=[]))
    assert "no page address in the record" in bill and "54SCMAOC_SCF_X" in bill and "names an address by its shape" in bill
    assert "withdrawn by the source" in panes.row_pane(ctx(v, item(served=False), same_words=[]))


def test_an_archived_page_cites_its_address_and_the_archive_s_copy():
    v = cat.BY_NAME["parliament_wayback_pages"]
    r = page()
    assert panes.title_of(v, r) == "Submissions called for · archived 2007-05-16"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert f'href="{OLD}"' in html and f'href="{SNAP}"' in html and "2007-05-16T10:22:14Z" in html
    assert "The committee calls for submissions." in html and "263" in html and "did not fetch parliament.nz" in html
    assert "names an address by its shape" in panes.row_pane(ctx(v, page(text_names_address=True), same_words=[]))
    assert "version taken last, of 4" in panes.row_pane(ctx(v, page(versions=4), same_words=[]))
