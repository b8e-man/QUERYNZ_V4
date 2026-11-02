"""registers/ministers_diaries: the attendees split (attendees.py), by rules, on the shapes the releases print
(measured 2 November 2026 on the 191,643 entries with an attendees text; private people's names replaced by made-up
ones of the same shape, public bodies and ministers as printed). Each case pins the rows' attendee text, kind and
organisation part; every split reconciles with its text; and each rule is shown load-bearing by a mutant that breaks
it. No database."""
import re

import pytest

from registers.ministers_diaries import attendees as A, check, read

LANE_TEXT = "Chief Executive, an association"


def rows(text):
    got, why = A.split(text)
    assert not why, why
    assert A.joined(got) == text and A.reconciles(text, got)
    assert [r["position"] for r in got] == list(range(1, len(got) + 1))
    return [(r["attendee"], r["kind"], r["organisation"]) for r in got]


@pytest.mark.parametrize("text,want", [
    # the officials boilerplate: a group, and the Crown's own group names no body
    ("Officials", [("Officials", "group", None)]),
    ("MBIE Officials", [("MBIE Officials", "group", None)]),
    ("Cabinet Committee Members", [("Cabinet Committee Members", "crown", "Cabinet Committee Members")]),
    ("Invited guests", [("Invited guests", "group", None)]),
    ("Media", [("Media", "group", None)]),
    ("Trade and Investment", [("Trade", "group", None), ("Investment", "group", None)]),
    # separators, `and`, titles
    ("Hon Doocey and Officials", [("Hon Doocey", "person", None), ("Officials", "group", None)]),
    ("Officials, and Staff", [("Officials", "group", None), ("Staff", "group", None)]),
    ("DPMC officials; PMO advisors", [("DPMC officials", "group", None), ("PMO advisors", "group", None)]),
    ("Hon Salesa and Genter; Dr Ashley Bloomfield and Ministry of Health officials",
     [("Hon Salesa", "person", None), ("Genter", "person", None), ("Dr Ashley Bloomfield", "person", None),
      ("Ministry of Health officials", "crown", "Ministry of Health officials")]),
    ("Hons Willis, Bishop, Jones, Stanford & Upston",
     [("Hons Willis", "person", None), ("Bishop", "person", None), ("Jones", "person", None),
      ("Stanford", "person", None), ("Upston", "person", None)]),
    ("PM, Woods, Parker", [("PM", "role", None), ("Woods", "person", None), ("Parker", "person", None)]),
    ("Mayor Jane Example, CEO of Kaikoura District Council, and Stuart Smith MP",
     [("Mayor Jane Example, CEO of Kaikoura District Council", "person", "Kaikoura District Council"),
      ("Stuart Smith MP", "person", None)]),
    # Name (Organisation), Name, Organisation
    ("Mary Example (CE, Te Puni Kōkiri)", [("Mary Example (CE, Te Puni Kōkiri)", "person", "Te Puni Kōkiri")]),
    ("Hon Carmel Sepuloni (MP for Kelston), Health West team",
     [("Hon Carmel Sepuloni (MP for Kelston)", "person", None), ("Health West team", "group", "Health West")]),
    ("Glen Example, Acting Chief Executive, Te Arawhiti",
     [("Glen Example, Acting Chief Executive, Te Arawhiti", "person", "Te Arawhiti")]),
    ("Clare Example, ANZSA & relevant officials", [("Clare Example, ANZSA", "person", "ANZSA"), ("relevant officials", "group", None)]),
    ("Matt Example, CEO and Jenna Example, Corporate Affairs General Manager",
     [("Matt Example, CEO", "person", None), ("Jenna Example, Corporate Affairs General Manager", "person", None)]),
    ("Corin Dann, RNZ", [("Corin Dann, RNZ", "person", "RNZ")]),
    ("Edward Example, Chair NZCA;", [("Edward Example, Chair NZCA", "person", "NZCA")]),
    ("Chris Example, Heather Example, Greg Example",
     [("Chris Example", "person", None), ("Heather Example", "person", None), ("Greg Example", "person", None)]),
    # a group's body, a body named alone
    ("Fonterra staff", [("Fonterra staff", "group", "Fonterra")]),
    ("Representatives of Fonterra; MPI Officials", [("Representatives of Fonterra", "group", "Fonterra"), ("MPI Officials", "group", None)]),
    ("Kiwibank, Spark and Fonterra", [("Kiwibank", "organisation", "Kiwibank"), ("Spark", "organisation", "Spark"),
                                      ("Fonterra", "organisation", "Fonterra")]),
    ("Auckland Council and Ports of Auckland", [("Auckland Council", "organisation", "Auckland Council"),
                                                ("Ports of Auckland", "organisation", "Ports of Auckland")]),
    ("Polly and Grant, More FM", [("Polly", "person", None), ("Grant", "person", None), ("More FM", "organisation", "More FM")]),
    # an `and`, `&` or `+` inside a body's name, and no spaced separator
    ("Ernst & Young", [("Ernst & Young", "organisation", "Ernst & Young")]),
    ("Fisher & Paykel Healthcare", [("Fisher & Paykel Healthcare", "organisation", "Fisher & Paykel Healthcare")]),
    ("Forest & Bird, Fish & Game", [("Forest & Bird", "organisation", "Forest & Bird"), ("Fish & Game", "organisation", "Fish & Game")]),
    ("Mental Health & Wellbeing Commission", [("Mental Health & Wellbeing Commission", "organisation", "Mental Health & Wellbeing Commission")]),
    ("Energy Efficiency & Conservation Authority",
     [("Energy Efficiency & Conservation Authority", "organisation", "Energy Efficiency & Conservation Authority")]),
    ("Chartered Accountants Australia and NZ",
     [("Chartered Accountants Australia and NZ", "organisation", "Chartered Accountants Australia and NZ")]),
    ("Q&A", [("Q&A", "organisation", "Q&A")]),
    ("TVNZ Q+A", [("TVNZ Q+A", "organisation", "TVNZ Q+A")]),
    ("Hon Andrew Hoggard + Officials", [("Hon Andrew Hoggard", "person", None), ("Officials", "group", None)]),
    ("Hons. Robertson, Woods, Parker + Officials",
     [("Hons. Robertson", "person", None), ("Woods", "person", None), ("Parker", "person", None), ("Officials", "group", None)]),
    # the Crown's own bodies, by name or initials; a body's name with a comma in it
    ("Ministry of Business, Innovation and Employment",
     [("Ministry of Business, Innovation and Employment", "crown", "Ministry of Business, Innovation and Employment")]),
    ("VA, NZDF", [("VA", "crown", "VA"), ("NZDF", "crown", "NZDF")]),
    ("NZ Trade and Enterprise", [("NZ Trade and Enterprise", "crown", "NZ Trade and Enterprise")]),
    # the release's withholding, never split
    ("Withheld under s.6 (a) Withheld under s.6 (a)", [("Withheld under s.6 (a) Withheld under s.6 (a)", "withheld", None)]),
    ("s9(2)(a)", [("s9(2)(a)", "withheld", None)]),
])
def test_each_shape_splits_by_the_rules(text, want):
    assert rows(text) == want


def test_the_crown_flag_marks_an_organisation_part_that_is_the_crown_s_own():
    got = {r["attendee"]: r["crown"] for r in A.split("Mary Example (CE, Te Puni Kōkiri); Corin Dann, RNZ; MPI; Fonterra")[0]}
    assert got == {"Mary Example (CE, Te Puni Kōkiri)": True, "Corin Dann, RNZ": False, "MPI": True, "Fonterra": False}


def test_titles_come_off_the_fold_and_the_fold_is_the_scans():
    r = A.split("Rt Hon Jane Example MP")[0][0]
    assert r["attendee"] == "Rt Hon Jane Example MP" and r["folded"] == "janeexample"
    assert A.fold("Ngāti Example Holdings Limited") == "ngatiexampleholdings"
    assert A.fold("Example (2019) Ltd") == "example2019"


def test_separators_left_at_either_end_are_kept_on_the_rows_and_nothing_is_lost():
    for text in ("Edward Example, Chair NZCA;", "; Officials", "Officials, , and Staff", "Hon Example and"):
        got, why = A.split(text)
        assert not why and A.joined(got) == text, text


def test_an_unbalanced_bracket_sets_the_entry_aside_with_its_reason():
    assert A.split("Hon Example (a") == ([], "a bracket left open")
    assert A.split("Hon Example a), Officials") == ([], "a closing bracket with none open")
    assert A.split(None) == ([], "") and A.split("  ") == ([], "")


def test_a_separator_inside_a_bracket_never_splits():
    assert rows("Jane Example (Chair, Example Trust and Example Society), Officials") == [
        ("Jane Example (Chair, Example Trust and Example Society)", "person", "Example Trust and Example Society"),
        ("Officials", "group", None)]


# ── mutants: each rule load-bearing ──────────────────────────────────────────

def test_the_reconciliation_catches_a_lost_a_doubled_and_a_moved_attendee():
    text = "Kiwibank, Spark and Fonterra"
    good = A.split(text)[0]
    lost = good[:-1]
    doubled = good + [dict(good[-1], sep_before=", ")]
    moved = [dict(good[1], sep_before=""), dict(good[0], sep_before=", ")] + good[2:]
    assert A.reconciles(text, good)
    for bad in (lost, doubled, moved):
        assert not A.reconciles(text, bad)


def test_a_body_name_with_a_separator_splits_without_the_keep_list(monkeypatch):
    monkeypatch.setattr(A, "KEEP", re.compile(r"(?!x)x"))
    assert len(A.split("Ministry of Business, Innovation and Employment")[0]) == 3
    assert len(A.split("Forest and Bird, Fish and Game")[0]) == 4


def test_officials_boilerplate_reads_as_a_body_without_the_group_words(monkeypatch):
    monkeypatch.setattr(A, "GROUP_WORDS", frozenset())
    monkeypatch.setattr(A, "CROWN_GROUP", frozenset())
    assert A.split("Fonterra staff")[0][0]["organisation"] == "Fonterra staff"


def test_a_person_s_organisation_is_lost_without_the_name_comma_rule(monkeypatch):
    monkeypatch.setattr(A, "is_person", lambda s: False)
    assert [r["organisation"] for r in A.split("Corin Dann, RNZ")[0]] == ["Corin Dann", "RNZ"]


def test_a_surname_list_reads_as_bodies_without_the_title_context(monkeypatch):
    monkeypatch.setattr(A, "is_surname", lambda s: False)
    assert [(r["attendee"], r["organisation"]) for r in A.split("Hons Willis, Bishop")[0]] == [("Hons Willis, Bishop", "Bishop")]


# ── the reading carries the rows, cited to the entry ─────────────────────────

def test_the_reading_carries_each_attendee_cited_to_its_entry_and_sets_aside_an_unsplit_text():
    from registers.ministers_diaries.tests.test_ministers_diaries import _read, _rec
    res = _read(_rec(1, attendees="Hon Doocey and Officials"), _rec(2, attendees="Hon Example (a"),
                _rec(3, attendees=None), _rec(4, attendees="A Person, 12 Example Road, Town; Chief Executive"))
    by = {}
    for r in res.attendees:
        by.setdefault(r["entry"], []).append(r)
    assert [r["key"] for r in by["1"]] == ["1/1", "1/2"] and res.attendees_set_aside == [("2", "a bracket left open")]
    assert "3" not in by and len(by["4"]) == 4                   # the flagged entry's attendees are carried, flagged by the view
    e1 = next(e for e in res.entries if e["key"] == "1")
    for r in by["1"]:
        assert r["document"] == e1["document"] and r["place"].startswith("record: attendees, attendee ")
        assert r["reader"] == A.READER and r["profile"] == read.PROFILE
    assert res.counts["attendee rows"] == 6 and res.counts["attendees set aside"] == 1


def _held(**kw):
    h = {"cursor": 1000, "arrivals": 1000, "documents": 1100, "caught": 0, "entries": 1000, "releases": 10,
         "older versions": 100, "files set aside": 0, "set aside": 0, "fields unread": 0, "words": 50000,
         "release entries": 1000, "releases miscounted": 0, "entries with no release": 0,
         "releases naming more than one minister": 0, "entries with an attendees text": 900, "entries split": 896,
         "entries set aside from the split": 4, "entries split and set aside": 0, "attendee rows of no entry": 0,
         "entries not reconciled": 0, "entries with a gap in positions": 0, "attendee rows": 1300}
    h.update(kw)
    return h


def test_the_check_names_each_attendee_failure():
    o = {"records": 1000, "n_docs": 1000, "corpus_words": 50100}
    assert check.judge(_held(), o) == []
    assert check.judge(_held(**{"entries split": 895}), o) == \
        ["attendees: 900 entries with an attendees text, but 895 split and 4 set aside"]
    for k in ("entries split and set aside", "attendee rows of no entry", "entries not reconciled",
              "entries with a gap in positions"):
        assert check.judge(_held(**{k: 2}), o) == [f"attendees: 2 {k}"], k
