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
