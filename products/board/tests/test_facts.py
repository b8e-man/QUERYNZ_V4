"""Ruling 117 (1): the dossier folds the rows that say the same thing about the
entity into one entry, by what the row says (body, role, kind of record),
never by view, on fixtures shaped as Lloyd Budd's rows are on the live tables:
a director and a shareholder of one company, a charity trustee, five Gazette
celebrant lists, a candidacy."""
import datetime as dt
import re

from products.board import catalogue as cat
from products.board import facts

V = cat.BY_NAME
CO = (V["companies"], {"key": "companies/9429", "name": "BUDD CONSULTANCY LIMITED"})
CH = (V["charities"], {"key": "charities/1", "name": "Keystone New Zealand Property Education Trust"})


def director(key, on, latest=True, ended=None):
    return ("companies:" + key, V["directors"], {"key": key, "entity_key": "companies/9429", "full_name": "Lloyd Sam BUDD",
                                                 "role_type": "DIRECTOR", "appointed_on": on, "ended_on": ended, "in_latest": latest})


def celebrant(notice, published, action="annual list", statute="Marriage Act 1955 s 11"):
    key = f"gazette/{notice}/celebrant/ef45"
    return ("gazette:" + key, V["gazette_celebrants"], {"key": key, "surname": "Budd", "given_names": "Lloyd", "action": action,
                                                        "statute": statute, "published_on": published, "document": "a" * 64})


SHARE = ("companies:companies/9429/shareholder/ae0d", V["shareholders"],
         {"key": "companies/9429/shareholder/ae0d", "entity_key": "companies/9429", "name": "Lloyd Sam BUDD", "shares": 100, "in_latest": True})
TRUSTEE = ("charities:charities/officers/1684473", V["charity_officers"],
           {"key": "charities/officers/1684473", "charity_key": "charities/1", "full_name": "Lloyd Budd", "role": "Trustee",
            "status": "Qualified", "started_on": dt.date(2025, 3, 11)})
LISTS = [celebrant("2020-go4751", dt.date(2020, 10, 15), "publication"), celebrant("2020-go5675", dt.date(2020, 12, 18)),
         celebrant("2021-go5312", dt.date(2021, 12, 20)), celebrant("2022-go5474", dt.date(2022, 12, 22)),
         celebrant("2025-go486", dt.date(2025, 1, 30))]
CANDIDATE = ("house:ge-2026/budd-lloyd-sam/whangarei", V["candidates"],
             {"key": "ge-2026/budd-lloyd-sam/whangarei", "name": "BUDD, Lloyd Sam", "display_name": "Lloyd Sam BUDD",
              "party": "National Party", "electorate": "ge-2026/whangarei", "election": "ge-2026", "list_place": 60})


def dossier_of(rows):
    bodies = {}
    for _, v, r in rows:
        for i, rel in enumerate(v.relations):
            far = {"companies": CO, "charities": CH}.get(rel.view)
            if far and r.get(rel.column) == far[1]["key"]:
                bodies[(v.name, r["key"], i)] = far
    return {"rows": rows, "bodies": bodies,
            "referred": {("candidates", "electorate", "ge-2026/whangarei"): "Whangārei",
                         ("candidates", "election", "ge-2026"): "2026 General Election"}}


def said(fs):
    return [facts.sentence_text(f) for f in fs]


def test_lloyd_budd_s_rows_say_three_things_and_each_is_a_sentence_about_him():
    rows = [director("companies/9429/director/890a", dt.date(2025, 12, 4)), SHARE, TRUSTEE] + LISTS + [CANDIDATE]
    fs = facts.fold(dossier_of(rows))
    assert said(fs) == ["Marriage celebrant, listed 2020 to 2025",
                        "Trustee of Keystone New Zealand Property Education Trust since 11 March 2025",
                        "Director and shareholder of BUDD CONSULTANCY LIMITED since 4 December 2025",
                        "Candidate, Whangārei, 2026 General Election"]
    lists = facts.small(fs[0])
    assert lists.startswith("five Gazette lists: 15 October 2020, 18 December 2020") and "Marriage Act 1955 s 11" in lists
    both = facts.small(fs[2])
    assert "director, appointed on 4 December 2025" in both and "shareholder, 100 shares" in both
    assert facts.small(fs[3]) == "National Party, list place 60"


def test_a_director_of_one_company_across_filings_is_one_entry_its_filings_counted():
    rows = [director("companies/9429/director/53a5", dt.date(2022, 8, 15)), director("companies/9429/director/428f", dt.date(2026, 6, 17))]
    fs = facts.fold(dossier_of(rows))
    assert said(fs) == ["Director of BUDD CONSULTANCY LIMITED since 15 August 2022"]
    assert facts.small(fs[0]).startswith("two filings: appointed on 15 August 2022, appointed on 17 June 2026")


def test_a_role_ended_on_every_filing_reads_from_its_first_day_to_its_last():
    rows = [director("companies/9429/director/1", dt.date(2010, 5, 1), False, dt.date(2015, 6, 2))]
    assert said(facts.fold(dossier_of(rows))) == ["Director of BUDD CONSULTANCY LIMITED 1 May 2010 to 2 June 2015"]


def test_the_fold_is_by_what_the_row_says_never_by_view():
    removed = celebrant("2023-go1", dt.date(2023, 3, 1), "removal", "Marriage Act 1955 s 13")
    union = celebrant("2021-go9", dt.date(2021, 5, 1), "annual list", "Civil Union Act 2004 s 26 and 27")
    fs = facts.fold(dossier_of(LISTS + [removed, union]))
    assert said(fs) == ["Marriage celebrant, listed 2020 to 2025", "Civil union celebrant, listed 1 May 2021",
                        "Marriage celebrant, removed 1 March 2023"]
    other = ("charities:charities/officers/9", V["charity_officers"], dict(TRUSTEE[2], key="charities/officers/9", role="Secretary",
                                                                           started_on=dt.date(2019, 1, 2)))
    fs = facts.fold(dossier_of([TRUSTEE, other]))                                # one charity, two roles: one body, one entry
    assert said(fs) == ["Secretary and Trustee of Keystone New Zealand Property Education Trust since 2 January 2019"]


def test_a_view_no_line_names_says_its_own_title_and_folds_with_nothing():
    a = ("gazette:n/1", V["gazette_notices"], {"key": "n/1", "notice": "2020-go1", "title": "Land notice", "published_on": dt.date(2020, 1, 2)})
    b = ("gazette:n/2", V["gazette_notices"], {"key": "n/2", "notice": "2020-go1", "title": "Land notice", "published_on": dt.date(2020, 1, 2)})
    assert len(facts.fold(dossier_of([a, b]))) == 2


def test_no_entry_names_a_register_a_view_or_a_row_count():
    """Ruling 117 (2): read with the register's own values masked first (the lesson on presentation rules)."""
    rows = [director("companies/9429/director/890a", dt.date(2025, 12, 4)), SHARE, TRUSTEE] + LISTS + [CANDIDATE]
    values = {str(x) for _, _, r in rows for x in r.values() if x not in (None, "")} | {CO[1]["name"], CH[1]["name"],
                                                                                        "Whangārei", "2026 General Election"}
    for f in facts.fold(dossier_of(rows)):
        text = facts.sentence_text(f)
        for x in sorted(values, key=len, reverse=True):
            text = text.replace(x, "·")
        words = [name for name, _ in cat.REGISTERS] + [plain for _, plain in cat.REGISTERS] + [v.name for v in cat.VIEWS]
        assert not [w for w in words if re.search(r"\b" + re.escape(w) + r"\b", text, re.I) and len(w) > 4], text
        assert not re.search(r"\b\d+ rows?\b|\bregisters?\b|\bsingle-row\b", text), text


def test_the_citation_is_one_line_naming_the_register_and_each_document_once():
    fs = facts.fold(dossier_of(LISTS))
    line = facts.cite(fs[0], {"a" * 64: {"state": "held", "kind": "application/pdf"}})
    assert line.count('<div class="cite">') == 1 and line.startswith('<div class="cite">source: Gazette')
    assert line.count('class="source"') == 1                                      # five rows, one document


def test_what_he_is_reads_as_words_for_the_entity_card():
    pairs = [(v, r) for _, v, r in [director("companies/9429/director/890a", dt.date(2025, 12, 4)), SHARE, TRUSTEE]]
    assert facts.what_it_is(pairs) == "director and shareholder, charity trustee"
    assert facts.what_it_is([(V["gazette_celebrants"], LISTS[0][2])]) == "marriage celebrant"
    assert facts.what_it_is([(V["gazette_notices"], {})]) == ""
