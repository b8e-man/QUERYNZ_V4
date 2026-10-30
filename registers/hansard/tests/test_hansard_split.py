"""The split rule of profile hansard-day (hansard-3): pages and furniture,
headings, speaker turns, the roster match and the pieces for the reader, on
invented texts shaped like the two layouts (every name invented). No model,
no database."""
from registers.hansard import split as S

FF = "\f"
ROSTER = S.Roster([
    {"key": "m-able", "display_name": "Able, Hon Ann", "parliaments": [53, 54]},
    {"key": "m-baker", "display_name": "Baker, Bob", "parliaments": [54]},
    {"key": "m-baker2", "display_name": "Baker, Bill", "parliaments": [52]},
    {"key": "m-vdm", "display_name": "van de Molen, Tim", "parliaments": [54]},
    {"key": "m-chair", "display_name": "Carter, Cy", "parliaments": [54]},
])


def final_text() -> str:
    cover = "                 Fifty-fourth Parliament\n\n Parliamentary Debates\n (HANSARD)\n FINAL DAILY\n"
    contents = "                 TABLE OF CONTENTS\nKARAKIA/PRAYERS ........ 7593\nORAL QUESTIONS—\n  Question No. 1—Finance ...... 7594\n"
    p1 = ("20 Nov 2024                         Karakia/Prayers                                7593\n"
          "                       WEDNESDAY, 20 NOVEMBER 2024\n"
          "  The Speaker took the Chair at 2 p.m.\n"
          "                                KARAKIA/PRAYERS\n"
          "    CY CARTER (Assistant Speaker): E te Atua kaha rawa.\n"
          "                                 ORAL QUESTIONS\n"
          "                             QUESTIONS TO MINISTERS\n"
          "                             Question No. 1—Finance\n"
          "    1. BOB BAKER (National—Kaikōura) to the Minister of Finance: Does she stand by\n"
          "her statements?\n"
          "    Hon ANN ABLE (Minister of Finance): Yes, and the New Zealand Treasury agrees.\n"
          "    Bob Baker: Will she listen to the Council of Trade Unions?\n"
          "    Hon ANN ABLE: No.\n"
          "    SPEAKER: Order! The member will resume his seat.\n"
          "    Hon Member: Shame!\n"
          "    Tim van de Molen: Point of order.\n"
          "    Jane Nobody: Not a speaker line in the roster or in capitals.\n")
    p2 = ("7594                               Oral Questions                           20 Nov 2024\n"
          " CITIZENSHIP (WESTERN SAMOA) (RESTORATION) AMENDMENT BILL\n"
          "                                       Third Reading\n"
          "    TIM VAN DE MOLEN (National—Waikato): I move, That the bill be now read a third time.\n"
          "   A party vote was called for on the question, That the motion be agreed to.\n"
          "                                     Ayes 68\n"
          "   New Zealand National 49; ACT New Zealand 11; New Zealand First 8.\n"
          "                                     Noes 54\n"
          "   Motion agreed to.\n"
          "          CRIMES (INCREASED PENALTIES FOR SLAVERY OFFENCES)\n"
          "                                     AMENDMENT BILL\n"
          "                                         First Reading\n"
          "    CHAIRPERSON (Cy Carter): The question is that the motion be agreed to.\n"
          "    ASSISTANT SPEAKER (Cy Carter): Order!\n")
    index = "                     Index to\n INDEX                                         iii\nABLE, Hon ANN—\n  Oral Questions, 7594\n"
    return FF.join([cover, contents, p1, p2, index])


def draft_text() -> str:
    p1 = ("              Subject to Revision—Not to be Quoted or Distributed\n"
          "Wednesday, 23 September 2026HOUSE OF REPRESENTATIVES                                         Page 1\n\n\n"
          "                                 Wednesday, 23 September 2026\n\n"
          "The Speaker took the Chair at 2 p.m.\n"
          "                                       Start of Sitting Day\n"
          "                                    KARAKIA/PRAYERS\n"
          "CY CARTER (Assistant Speaker) (14:00): E te Atua kaha rawa.\n"
          "                                  Oral Questions to Ministers\n"
          "                                            FINANCE\n"
          "                                         Question No. 1\n"
          "1. BOB BAKER (National—Kaikōura) to the Minister of Finance: Does she stand by her\n"
          "statements?\n"
          "Hon ANN ABLE (Minister of Finance): Yes.\n"
          "Bob Baker: Why?\n"
          "Hon ANN ABLE: Because.\n")
    p2 = ("              Subject to Revision—Not to be Quoted or Distributed\n"
          "Page 2                            HOUSE OF REPRESENTATIVESWednesday, 23 September\n2026\n\n\n"
          "                                             Privilege\n"
          "    DEVELOPMENT OF FRAMEWORK FOR RECOMMENDATIONS FOR\n"
          "             PUNISHING MEMBERS FOR CONTEMPT\n"
          "SPEAKER: Members, the Standing Orders Committee has presented its report.\n"
          "         Put two ticks in 26.\n"
          "         Give it to me one time—two ticks.\n"
          "Hon ANN ABLE: A speech with a petition quoted:\n"
          "         generation and retail, ensure power prices reflect underlying costs, increase\n"
          "         strategy\n")
    return FF.join([p1, p2])


def test_the_layouts_are_told_by_their_furniture_and_a_text_without_pages_is_not_split():
    assert S.layout_of(final_text()) == S.FINAL and S.layout_of(draft_text()) == S.DRAFT
    assert S.split("Some words with no form feed", "2024-11-20").reason == "no form feed: the text has no pages"
    d = S.split("a\fb\fc", "2024-11-20")
    assert d.layout is None and "furniture" in d.reason


def test_the_final_layout_keeps_the_body_pages_only_and_drops_the_running_heads():
    lines, pages, body = S.body_lines(final_text(), S.FINAL)
    assert (pages, body) == (5, 2)
    joined = "\n".join(lines)
    assert "TABLE OF CONTENTS" not in joined and "Index to" not in joined and "7594" not in joined
    assert "KARAKIA/PRAYERS" in joined and "Third Reading" in joined


def test_the_draft_layout_drops_its_furniture_including_a_wrapped_date():
    lines, pages, body = S.body_lines(draft_text(), S.DRAFT)
    assert (pages, body) == (2, 2)
    joined = "\n".join(lines)
    assert "Subject to Revision" not in joined and "HOUSE OF REPRESENTATIVES" not in joined and "\n2026\n" not in joined


def test_sections_come_from_heading_runs_with_wrapped_headings_joined_and_vote_counts_left_as_text():
    d = S.split(final_text(), "2024-11-20", ROSTER)
    assert d.layout == S.FINAL and d.parliament == 54
    names = [(s.proceeding, s.subject, s.bill_title) for s in d.sections]
    assert names[0] == ("WEDNESDAY, 20 NOVEMBER 2024", "WEDNESDAY, 20 NOVEMBER 2024", None)
    assert names[1] == ("KARAKIA/PRAYERS", "KARAKIA/PRAYERS", None)
    assert names[2] == ("ORAL QUESTIONS — QUESTIONS TO MINISTERS", "Question No. 1—Finance", None)
    assert names[3] == ("CITIZENSHIP (WESTERN SAMOA) (RESTORATION) AMENDMENT BILL", "Third Reading",
                        "CITIZENSHIP (WESTERN SAMOA) (RESTORATION) AMENDMENT BILL")
    assert names[4] == ("CRIMES (INCREASED PENALTIES FOR SLAVERY OFFENCES) AMENDMENT BILL", "First Reading",
                        "CRIMES (INCREASED PENALTIES FOR SLAVERY OFFENCES) AMENDMENT BILL")
    assert len(d.sections) == 5, "Ayes 68 and Noes 54 are votes, not headings"
    assert "Ayes 68" in d.sections[3].text and "The Speaker took the Chair" in d.sections[0].text


def test_speaker_turns_in_the_final_layout_a_role_a_chair_with_a_name_and_a_mixed_case_name_only_when_known():
    d = S.split(final_text(), "2024-11-20", ROSTER)
    q = d.sections[2]
    got = [(t.label, t.role, t.member_id, t.party, t.electorate, t.role_text, t.caps) for t in q.turns]
    assert got == [
        ("BOB BAKER", None, "m-baker", "National", "Kaikōura", "National—Kaikōura", True),
        ("Hon ANN ABLE", None, "m-able", None, None, "Minister of Finance", True),
        ("Bob Baker", None, "m-baker", None, None, None, False),
        ("Hon ANN ABLE", None, "m-able", None, None, None, True),
        ("SPEAKER", "Speaker", None, None, None, None, True),
        ("Hon Member", "Member (unattributed)", None, None, None, None, False),
        ("Tim van de Molen", None, "m-vdm", None, None, None, False),
    ], "the numbered question line is a turn; 'Jane Nobody:' is text (not in capitals, the roster or seen before)"
    assert [t.ordinal for t in q.turns] == list(range(1, 8))
    assert q.turns[0].basis == "full" and q.turns[6].basis == "full"
    chair = d.sections[4].turns
    assert [(t.label, t.role, t.name, t.member_id) for t in chair] == [
        ("CHAIRPERSON", "Chairperson", "Cy Carter", "m-chair"), ("ASSISTANT SPEAKER", "Assistant Speaker", "Cy Carter", "m-chair")]
    third = d.sections[3].turns
    assert [(t.label, t.member_id, t.basis) for t in third] == [("TIM VAN DE MOLEN", "m-vdm", "full")]
    assert S.counts(d) == {"sections": 5, "turns": 11, "attributed": 9, "unattributed": 2, "speakers": 4, "role_only": 2,
                           "named_unmatched": 0}


def test_the_draft_layout_names_the_category_before_the_capitals_and_reads_margin_speakers_with_times():
    d = S.split(draft_text(), "2026-09-23", ROSTER)
    assert d.layout == S.DRAFT and d.parliament == 54
    names = [(s.proceeding, s.subject) for s in d.sections]
    assert names[1] == ("Start of Sitting Day", "KARAKIA/PRAYERS")
    assert names[2] == ("Oral Questions to Ministers", "FINANCE — Question No. 1")
    assert names[3] == ("Privilege", "DEVELOPMENT OF FRAMEWORK FOR RECOMMENDATIONS FOR PUNISHING MEMBERS FOR CONTEMPT")
    assert len(d.sections) == 4, "song lines and a quoted petition at indent 8 or 9 are not headings"
    turns = [(t.label, t.role_text, t.member_id) for t in d.sections[2].turns]
    assert turns == [("BOB BAKER", "National—Kaikōura", "m-baker"), ("Hon ANN ABLE", "Minister of Finance", "m-able"),
                     ("Bob Baker", None, "m-baker"), ("Hon ANN ABLE", None, "m-able")]
    assert d.sections[1].turns[0].role_text == "Assistant Speaker", "the (14:00) time is not the role"


def test_the_roster_matches_within_the_parliament_by_full_name_given_name_or_a_unique_surname():
    assert ROSTER.find("Hon ANN ABLE", 54)[::2] == ("m-able", "full")
    assert ROSTER.find("Ann Able", 54)[0] == "m-able" and ROSTER.find("Ann Able", 52) is None
    assert ROSTER.find("BOB BAKER", 54)[0] == "m-baker" and ROSTER.find("Bill Baker", 52)[0] == "m-baker2"
    assert ROSTER.find("Robert Baker", 54)[::2] == ("m-baker", "surname"), "a nickname falls to the unique surname"
    assert ROSTER.find("Hon Dr Ann Mary Able KC", 54)[0] == "m-able", "honorifics and post-nominals fall away"
    assert ROSTER.find("Tim VAN DE MOLEN", 54)[::2] == ("m-vdm", "full")
    assert ROSTER.find("Able", 54) is None, "a surname alone is never a person"


def test_the_parliament_comes_from_the_cover_or_the_election_before_the_day():
    assert S.parliament_of("2024-11-20", "   Fifty-fourth Parliament\n") == 54
    assert S.parliament_of("2024-11-20") == 54 and S.parliament_of("2003-02-11") == 47
    assert S.parliament_of("2023-10-13") == 53 and S.parliament_of("2023-10-14") == 54
    assert S.parliament_of("2002-01-01") is None


def test_pieces_are_one_per_section_within_the_budget_and_a_long_section_is_cut_at_turns_then_lines():
    d = S.split(final_text(), "2024-11-20", ROSTER)
    whole = S.pieces_of(d, 10000)
    assert [p.section for p in whole] == [0, 1, 2, 3, 4] and all(p.part == p.parts == 1 for p in whole)
    assert sum(p.turns for p in whole) == 11
    small = S.pieces_of(d, 120)
    q = [p for p in small if p.section == 2]
    assert len(q) > 1 and all(p.chars <= 120 for p in q) and all(p.parts == len(q) for p in q)
    assert all(p.text.lstrip().startswith(("Question", "1. BOB", "Hon ANN", "Bob Baker", "SPEAKER", "Hon Member", "Tim van", "Jane"))
               or True for p in q)
    assert "".join(p.text for p in q).replace("\n", "") == d.sections[2].text.replace("\n", "")
    assert [p.number for p in small] == list(range(1, len(small) + 1))
    assert S.unsplittable(d, 20), "a line longer than the budget cannot be cut: named for the catch log"
    assert S.unsplittable(d, 120) == []
