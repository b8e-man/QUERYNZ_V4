"""The deterministic name pass (31 October 2026): forms from a register row, the scan over a text, longest first, offsets
into the original text, macrons and case folded. No database."""
from links import sightings as S


def test_a_persons_forms_are_the_full_name_and_given_family_and_one_word_is_no_form():
    assert S.forms_of("person", "Zhaoqin FAIR", "Zhaoqin", None, "FAIR") == {"zhaoqin fair"}
    assert S.forms_of("person", "John Michael KEY", "John Michael", None, "Key") == {"john michael key", "john key"}
    assert S.forms_of("person", "Al Li", "Al", None, "Li") == set(), "under MIN_CHARS"
    assert S.forms_of("organisation", "Fonterra", None, None, None) == set(), "one word finds noise"
    assert S.forms_of("organisation", "Te Pāti Māori", None, None, None) == {"te pati maori"}


def test_the_scan_finds_the_longest_form_with_offsets_into_the_printed_text():
    forms = {"john key": "person", "john michael key": "person", "te pati maori": "organisation", "new zealand police": "organisation"}
    text = "Hon JOHN Michael Key met Te Pāti Māori, then John Key spoke; the New Zealand  Police said."
    hits = S.scan(text, forms)
    assert [h[0] for h in hits] == ["john michael key", "te pati maori", "john key", "new zealand police"]
    assert [text[a:b] for _, a, b in hits] == ["JOHN Michael Key", "Te Pāti Māori", "John Key", "New Zealand  Police"]


def test_no_form_no_sighting_and_a_partial_name_is_not_one():
    assert S.scan("Johnny Keys and John alone", {"john key": "person"}) == []


def test_a_role_or_a_phrase_filed_as_a_name_is_no_form():
    for phrase in ("The Project", "Madam CHAIR", "Second Respondent", "Chief Executive", "Rt Hon", "The Court", "New Zealand"):
        assert S.forms_of("organisation", phrase, None, None, None) == set(), phrase
    assert S.forms_of("organisation", "New Zealand First", None, None, None) == {"new zealand first"}
    assert S.forms_of("organisation", "Supreme Court of New Zealand", None, None, None) == set()


def test_every_lane_dates_its_documents_and_the_view_carries_the_date():
    from links import sightings as S
    assert set(S.DATED) == set(S.LANES), "a lane scanned with no date source"
    assert all(q.count("%s") == 0 and " GROUP BY 1" in q for q in S.DATED.values()), "one date per document"
    view = S.DDL[S.DDL.index("CREATE OR REPLACE VIEW pub.name_sightings"):]
    assert "d.dated" in view and "LEFT JOIN links.sightings_done d" in view, "the view carries the document's date"
    assert all(q.count(",") >= 2 for q in S.STREAMED.values()), "a streamed lane reads its date with its text"


def test_a_short_form_no_longer_swallows_the_start_of_a_name_and_a_name_inside_a_longer_one_is_no_sighting():
    forms = {"dr duncan": "person", "duncan webb": "person", "john michael key": "person", "michael key": "person"}
    text = "Gully—\n   Hon Dr Duncan Webb: Are you sure? JOHN Michael Key replied."
    hits = S.scan(text, forms)
    assert [h[0] for h in hits] == ["dr duncan", "duncan webb", "john michael key"]
    assert [text[a:b] for _, a, b in hits] == ["Dr Duncan", "Duncan Webb", "JOHN Michael Key"]


def test_a_title_or_office_filed_in_front_of_the_given_names_is_no_part_of_a_persons_form():
    assert S.forms_of("person", "Dr Andrew WEST", "Dr Andrew", None, "West") == {"andrew west"}
    assert S.forms_of("person", "Dr WEST", "Dr", None, "West") == set(), "a title and a surname is no name"
    assert S.forms_of("person", "Judge GIBSON", "Judge", None, "Gibson") == set()
    assert S.forms_of("person", "Rt Hon Sir John KEY", "Rt Hon Sir John", None, "Key") == {"john key"}
    assert S.forms_of("organisation", "Justice and Electoral Committee", None, None, None) == {"justice and electoral committee"}


def test_a_hyphenated_given_name_keeps_its_whole_first_name_in_the_given_and_family_form():
    assert S.forms_of("person", "Aiden-Lee JOHNSON", "Aiden-Lee", "Mark", "Johnson") == {"aiden lee mark johnson", "aiden lee johnson"}
