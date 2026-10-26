"""The three Hansard views as registers/hansard/pane.md states them: a
sitting day titled with its Parliament and volume, citing the transcript's
address; a section's text whole in its own pane alone, "no text held" where
none was captured, never in a results hit or the table; a speech turn
titled with the old roster's name and the label as read by the old estate,
a role-only turn the role and never a person; every row's two lines; no
pointer and no edge to the House's member row (pub.members carries no
member id: a name match would be a link made by looking)."""
import datetime as dt

from products.board import catalogue as cat
from products.board import panes, search
from products.board.tests.test_panes import ctx

URL = "https://hansard.parliament.nz/hansard-transcript/2024-11-20"
CITE = {"source_note": "taken from the old estate's tables; original not held", "document": "ab" * 32, "page": 1,
        "read_from": "text", "reader": "export", "profile": "hansard-export", "url": URL}


def sitting(**kw):
    r = {"key": "2024-11-20", "sitting_on": dt.date(2024, 11, 20), "parliament": 54, "volume": 780, "progress": "Corrected",
         "sections": 30, "turns": 345, "attributed": 300, "unattributed": 45, "speakers": 60, "index_lastmod": None,
         "index_fetched": None, "place": "sitting 2024-11-20", **CITE}
    r.update(kw)
    return r


def section(**kw):
    r = {"key": "2024-11-20/10", "sitting_on": dt.date(2024, 11, 20), "section_index": 10, "parliament": 54, "volume": 780,
         "proceeding": "Oral Questions", "subject": "Questions to Ministers", "bill_title": None, "bill_id": None,
         "progress": "Corrected", "text": "Question one.\nAnswer one, " + "and more " * 20, "chars": 200, "turns": 12,
         "place": "sitting 2024-11-20 section 10", **CITE}
    r.update(kw)
    return r


def turn(**kw):
    r = {"key": "2024-11-20/10/10", "sitting_on": dt.date(2024, 11, 20), "section_index": 10, "ordinal": 10,
         "member_id": "61725fea-0000", "member_name": "Doe, Jane", "label_as_read": "Hon JANE DOE", "role": "",
         "proceeding": "Oral Questions", "subject": "Questions to Ministers", "bill_title": None, "bill_id": None,
         "progress": "Corrected", "place": "sitting 2024-11-20 section 10 turn 10", **CITE}
    r.update(kw)
    return r


def test_the_register_sits_by_the_house_and_takes_the_house_s_colour():
    regs = [r for r, _ in cat.REGISTERS]
    assert regs.index("hansard") == regs.index("mp_interests") + 1
    assert dict(cat.REGISTERS)["hansard"] == "Hansard: who spoke in Parliament"
    assert cat.FAMILY_OF["hansard"] == "the House" and cat.REGISTER_COLOUR["hansard"] == cat.REGISTER_COLOUR["house"]
    assert "hansard" not in dict(cat.NOT_HELD)
    assert cat.main_view_of("hansard") == "hansard_sittings"
    assert [v.name for v in cat.views_of("hansard")] == ["hansard_sittings", "hansard_sections", "hansard_speeches"]


def test_a_sitting_day_is_titled_with_its_parliament_and_volume_and_cites_the_transcript():
    v = cat.BY_NAME["hansard_sittings"]
    assert panes.title_of(v, sitting()) == "20 November 2024 · Parliament 54, volume 780"
    html = panes.row_pane(ctx(v, sitting(), same_words=[]))
    assert "Corrected" in html and "role-only turns" in html and f'href="{URL}"' in html
    assert "original not held" in html and "held at 23 September 2026" in html
    assert "person: the group" not in html


def test_a_section_s_text_is_whole_in_its_pane_and_never_in_a_hit_or_the_table():
    v = cat.BY_NAME["hansard_sections"]
    r = section()
    assert panes.title_of(v, r) == "Questions to Ministers · 20 November 2024"
    pane = panes.row_pane(ctx(v, r, same_words=[]))
    assert "Text as captured" in pane and "Question one.\nAnswer one, " + "and more " * 20 in pane
    assert "shown on the board only" in pane
    hit = panes.hit("", v, r, [])
    table = panes.table_pane("", v, 1, [r], search.FIRST)
    assert "Question one" not in hit and "Question one" not in table
    assert all(c != "text" for _, c in v.fields) and "text" not in v.search


def test_a_section_captured_with_no_text_says_no_text_held():
    v = cat.BY_NAME["hansard_sections"]
    for empty in (None, ""):
        assert "no text held" in panes.row_pane(ctx(v, section(text=empty, chars=0), same_words=[]))


def test_a_turn_is_titled_with_the_roster_name_and_the_label_as_read_by_the_old_estate():
    v = cat.BY_NAME["hansard_speeches"]
    assert panes.title_of(v, turn()) == 'Doe, Jane · "Hon JANE DOE" as read by the old estate · 20 November 2024'
    html = panes.row_pane(ctx(v, turn(), same_words=["jane", "doe"]))
    assert "the old roster&#x27;s name" in html and "presence on the record, not advocacy" in html
    names = cat.fields_of(v).names
    assert [(n.whole, n.order) for n in names] == [("member_name", cat.FAMILY_GIVEN)]


def test_a_role_only_turn_shows_the_role_and_never_a_person():
    v = cat.BY_NAME["hansard_speeches"]
    r = turn(member_id=None, member_name=None, label_as_read="SPEAKER", role="Speaker", key="2024-11-20/10/12")
    assert panes.title_of(v, r) == "Speaker · 20 November 2024"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "person: the group" not in html and v.kind != "person"
    member = v.joins[1]
    assert member.label == "This member's turns" and [r.get(own) for _, own in member.pairs()] == [None]   # no member id: no member's turns asked


def test_a_turn_names_no_house_member_row_and_draws_no_edge():
    for name in ("hansard_sittings", "hansard_sections", "hansard_speeches"):
        v = cat.BY_NAME[name]
        assert v.relations == () and cat.pointers(v) == {}
        assert v.note.startswith(cat.HANSARD_NOTE)


def test_a_two_column_join_asks_for_each_pair():
    seen = []

    class Conn:
        pass

    def rows(conn, sql, params):
        seen.append((sql, params))
        return []
    v = cat.BY_NAME["hansard_speeches"]
    real = search.db.rows
    search.db.rows = rows
    try:
        out = search.children(Conn(), v, turn())
    finally:
        search.db.rows = real
    assert "where sitting_on = %s and section_index = %s order by section_index" in seen[0][0]
    assert seen[0][1] == (dt.date(2024, 11, 20), 10, 200)
    assert "where member_id = %s order by sitting_on" in seen[1][0] and seen[1][1] == ("61725fea-0000", 200)
    assert [total for _, total, _ in out] == [0, 0]
