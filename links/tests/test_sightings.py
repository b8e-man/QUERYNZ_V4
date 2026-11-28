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
    assert "s.document || '/' || s.lane || '/' || s.start_at AS key" in view, "a sighting's key, for the board (2 November 2026)"
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
    assert S.forms_of("person", "The Rt Hon Sir William Francis BIRCH", "The", "Rt Hon Sir William Francis", "BIRCH") == \
        {"william francis birch", "william birch"}, "a title the Companies Office runs on into the middle names"
    assert S.forms_of("person", "Mrs.chandanie Priya MADDUMAGE", "Mrs.chandanie", "Priya", "MADDUMAGE") == \
        {"chandanie priya maddumage", "chandanie maddumage"}


def test_the_regions_and_each_district_linz_lists_are_places():
    class C:
        def execute(self, *_):
            class R:
                def fetchall(self):
                    return [("Hawke Bay",), ("Central Hawke's Bay District, Hastings District",), ("Area Outside Territorial Authority",)]
            return R()
    p = S.places(C())
    assert {"hawke s bay", "west coast", "tamaki makaurau", "hastings district", "hastings", "central hawke s bay"} <= p
    assert "area outside territorial authority" not in p


def test_a_hyphenated_given_name_keeps_its_whole_first_name_in_the_given_and_family_form():
    assert S.forms_of("person", "Aiden-Lee JOHNSON", "Aiden-Lee", "Mark", "Johnson") == {"aiden lee mark johnson", "aiden lee johnson"}


class _Catalogue:
    """Answers the stamp query with what the catalogue holds; records every statement."""

    def __init__(self, comment):
        self.comment, self.sql = comment, []

    def execute(self, sql, params=()):
        self.sql.append(sql)
        if sql.startswith("COMMENT ON TABLE links.sightings_done"):
            self.comment = sql.split("'")[1]

        class R:
            def __init__(s, row):
                s.row = row

            def fetchone(s):
                return s.row
        return R((self.comment,) if "obj_description" in sql else None)


def test_the_ddl_runs_once_and_a_lane_whose_ddl_is_current_takes_no_lock():
    # 7 November 2026: four lane jobs ran the DDL at their start together and two deadlocked
    from links import sightings as S
    fresh = _Catalogue(None)
    assert S.ensure_tables(fresh) is True
    assert S.DDL in fresh.sql and any("pg_advisory_xact_lock" in q for q in fresh.sql) and fresh.comment == S.DDL_STAMP
    again = _Catalogue(S.DDL_STAMP)
    assert S.ensure_tables(again) is False
    assert again.sql and all("obj_description" in q for q in again.sql)
    changed = _Catalogue("sightings ddl 0000000000000000")
    assert S.ensure_tables(changed) is True and S.DDL in changed.sql


def test_an_honorific_is_never_part_of_a_form_filed_whole():
    from links.sightings import forms_of
    assert forms_of("person", "Rt. Hon Trevor Mallard", None, None, None) == {"trevor mallard"}
    assert forms_of("person", "Hon Dr Duncan Webb", None, None, None) == {"duncan webb"}
    assert forms_of("organisation", "Dr Pharmacy Ltd", None, None, None) == {"dr pharmacy ltd"}


def test_a_judged_class_and_the_review_answers_become_the_judged_file(tmp_path):
    import json
    from links import forms_review as F
    (tmp_path / "answers").mkdir()
    (tmp_path / "name-forms-1.json").write_text(json.dumps({"questions": [
        {"id": "a", "form": "of the"}, {"id": "b", "form": "waitangi tribunal"}, {"id": "c", "form": "in their"}]}))
    (tmp_path / "answers" / "name-forms-1.json").write_text(json.dumps({"a": {"choice": "junk", "note": ""},
                                                                       "b": {"choice": "look", "note": ""}}))
    out = tmp_path / "judged.json"
    got = F.absorb(tmp_path, out)
    j = json.loads(out.read_text())
    assert j["of the"]["choice"] == "junk" and "waitangi tribunal" not in j and "in their" not in j
    assert j["social development"]["choice"] == "junk" and got["junk"] == 1 + len(F.CLASS_RULINGS)


def test_an_organisation_form_of_company_words_and_small_words_only_is_no_form():
    for f in ("is limited", "trustees of", "nz ltd", "co leader", "holdings limited"):
        assert S.company_words_only(f), f
    for f in ("fonterra co operative group ltd", "vector gas ltd", "waipareira trust", "new zealand law society", "one nz"):
        assert not S.company_words_only(f), f


def test_a_view_that_files_names_whole_is_no_parts_view_whatever_it_carries_after_them():
    assert "minister_diary_attendees" not in S.PARTS_VIEWS and "court_judgment_parties" not in S.PARTS_VIEWS
    assert "directors" in S.PARTS_VIEWS


def test_a_refreshed_review_set_keeps_every_answer_and_drops_only_an_unanswered_form_gone():
    # Arthur, 28 November 2026: name-forms-1 brought up to the rebuild, answers kept
    from links import forms_review as F
    q = lambda form, kind: F.question(form, kind, 1, 50, {"news": 50}, [])
    d = {"set": "name-forms-1", "questions": [q("of the", "person"), q("hon trevor mallard", "person"),
                                             q("callaghan innovation", "person"), q("john key", "person")]}
    answered = {F.qid("hon trevor mallard"), F.qid("callaghan innovation")}
    now = {"callaghan innovation": ("organisation", 40, 900, {"news": 900}), "john key": ("person", 15270, 72993, {})}
    out, n = F.refreshed(d, answered, now, {"john key": [("house", "members", "John KEY")]})
    forms = {x["form"]: x for x in out["questions"]}
    assert set(forms) == {"hon trevor mallard", "callaghan innovation", "john key"}       # "of the": gone, unanswered
    assert forms["hon trevor mallard"]["gone"] and forms["hon trevor mallard"]["id"] == F.qid("hon trevor mallard")
    assert forms["callaghan innovation"]["filed_as"] == "organisation" and forms["callaghan innovation"]["rows"] == 40
    assert forms["john key"]["filed"] == [{"register": "house", "view": "members", "name": "John KEY"}]
    assert n == {"kept": 1, "changed_kind": 1, "gone_dropped": 1, "gone_answered": 1}
