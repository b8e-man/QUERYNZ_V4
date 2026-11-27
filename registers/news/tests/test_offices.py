from registers.news import offices as O

TEXT = "Labour finance spokesperson Barbara Edmonds said the caretaker Health Minister Simeon Brown was wrong."


def test_the_gate_keeps_an_office_whose_words_and_fields_are_printed():
    good = {"who": "e1", "office": "spokesperson", "words": "Labour finance spokesperson", "portfolio": "finance",
            "body": "Labour", "party": "Labour", "electorate": None, "list": None, "qualifier": "current"}
    made = {**good, "words": "Caretaker Health Minister", "electorate": "Hamilton West"}
    stranger = {**good, "who": "e9"}
    kept, dropped = O.gate([good, made, stranger], TEXT, {"e1", "e2"})
    assert kept == [good]
    assert [d["rule"] for d in dropped] == ["electorate not in the text", "not a person of the article"]


def test_independent_is_a_party_the_text_need_not_print():
    o = {"who": "e1", "office": "member of parliament", "words": "Barbara Edmonds", "portfolio": None, "body": None,
         "party": "independent", "electorate": None, "list": None, "qualifier": "current"}
    assert O.gate([o], TEXT, {"e1"})[0] == [o]


def test_an_office_reads_as_one_line():
    o = {"who": "e2", "office": "minister", "words": "caretaker Health Minister", "portfolio": "Health", "body": None,
         "party": None, "electorate": None, "list": None, "qualifier": "caretaker"}
    assert O.describe(o, {"e2": "Simeon Brown"}) == "Simeon Brown: caretaker minister · portfolio Health"


def test_the_sample_is_the_sentences_that_hold_the_offices_marked():
    text = "HEADLINE: H\n\nA first line. Labour finance spokesperson Barbara Edmonds spoke. Nothing here. The caretaker Health Minister replied."
    runs = O.context_runs(text, [{"words": "caretaker Health Minister"}, {"words": "Labour finance spokesperson"}])
    assert [r["text"] for r in runs if r.get("mark")] == ["Labour finance spokesperson", "caretaker Health Minister"]
    assert "Nothing here" not in "".join(r["text"] for r in runs) and "A first line" not in "".join(r["text"] for r in runs)
