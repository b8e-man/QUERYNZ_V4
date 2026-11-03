"""Ruling 4 (Arthur, 3 November 2026): the links lane gathers a case's documents into one case by citation and case
number (judgments, case pages, media releases, transcripts, submissions), in its own table. A case is not a person
entity: it never merges people or companies. Invented values throughout."""
import inspect

from links import build, opportunities


def test_a_case_number_is_read_as_the_courts_print_it():
    assert build.case_number_key("SC 12/2020") == build.case_number_key("SC12/2020") == "SC12/2020"
    assert build.case_number_key("CIV-2019-404-001234") == build.case_number_key("civ-2019-404-1234") == "CIV-2019-404-1234"
    assert build.case_number_key("CA 12/2020") != build.case_number_key("SC 12/2020")
    assert build.case_number_key("  ") == ""


def test_documents_sharing_a_citation_or_a_case_number_are_one_case_and_the_case_is_its_smallest_document():
    keys = {"d3": build.case_keys(["[2020] NZHC 1"], ["CIV-2019-404-0012"], []),        # the judgment
            "d1": build.case_keys([], ["CIV-2019-404-12"], ["acme-v-kauri"]),            # the case page, by its number
            "d2": build.case_keys([], [], ["acme-v-kauri"]),                              # the media release, by the case page
            "d9": build.case_keys(["[2021] NZCA 5"], ["CA 1/2021"], []),                 # another case
            "d8": build.case_keys([], [], [])}                                             # nothing shared
    case = build.case_groups(keys)
    assert case == {"d1": "d1", "d2": "d1", "d3": "d1", "d9": "d9", "d8": "d8"}


def test_a_key_shared_by_more_documents_than_the_cap_joins_none():
    keys = {f"d{i}": build.case_keys([], ["CRI-2020"], []) for i in range(5)}
    assert set(build.case_groups(keys, cap=4).values()) == set(keys)          # each its own
    assert set(build.case_groups(keys, cap=5).values()) == {"d0"}


def test_a_case_touches_no_link_group_or_entity():
    src = inspect.getsource(build.build_cases)
    for table in (".links", ".groups", ".entities", ".rows"):
        assert f"{{s}}{table}" not in src, table
    assert "cases" not in inspect.getsource(build.components) and "cases" not in inspect.getsource(build.build_groups)


def test_the_register_names_the_case_rule_for_the_citation_and_the_case_number():
    assert build.RULE_CASE in opportunities.rule_ids()
    for field, key in (("citation", "citation"), ("case_numbers", "case_number")):
        e = opportunities.entry_for("courts-judgment", field, key)
        assert e.status == "rule" and e.rules == (build.RULE_CASE,), field
