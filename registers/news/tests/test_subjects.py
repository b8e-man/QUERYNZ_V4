"""The subjects pass's gate (registers.news.subjects): the article's own words, and inferred by stems."""
from registers.news import subjects as S

TEXT = ("HEADLINE: Hundreds of 3D-printed guns seized\n\nPolice found 300 3D-printed firearms. The footage showed "
        "the crowd crush in Seoul's Itaewon district in 2022.")


def test_a_name_is_in_the_text_by_its_stems_and_any_ending():
    assert S.stems("3D printing") == ["3d", "print"]
    assert S.names_in("3D printing", TEXT) and S.names_in("3D-printed firearms", TEXT)
    assert not S.names_in("the 2022 Seoul crowd crush", TEXT), "the order differs: inferred"
    assert S.names_in("illegal firearms", "illegal 3D-printed firearms"), "two words between are allowed"
    assert not S.names_in("illegal firearms", "illegal drugs were found beside the old firearms")


def test_the_gate_keeps_the_article_s_words_marks_inferred_and_drops_the_rest():
    kept, dropped = S.gate([
        {"name": "3D printing", "kind": "technology", "words": "3D-printed"},
        {"name": "the 2022 Seoul crowd crush", "kind": "event", "words": "the crowd crush in Seoul's Itaewon district"},
        {"name": "Call of Duty", "kind": "product_or_work", "words": "Call of Duty"},
        {"name": "3d  Printing", "kind": "technology", "words": "3D-printed"},
        {"name": "guns", "kind": "weapon", "words": "guns"},
    ], TEXT)
    assert [(k["name"], k["inferred"]) for k in kept] == [("3D printing", False), ("the 2022 Seoul crowd crush", True)]
    assert [d["rule"] for d in dropped] == ["its words are not in the article", "the same subject twice",
                                            "not a kind of subject: 'weapon'"]


def test_the_prompt_and_the_schema_name_the_same_kinds():
    assert S.SCHEMA["properties"]["subjects"]["items"]["properties"]["kind"]["enum"] == list(S.KINDS)
    for k in S.KINDS:
        assert f"- {k}:" in S.PROMPT
