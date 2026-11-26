"""links.news: an article's people and organisations, keyed as the registers' rows are."""
from links import news

GOT = {"entities": {"e1": {"name": "Chris Hipkins", "kind": "person", "forms": ["Chris Hipkins", "Hipkins"]},
                    "e2": {"name": "Fonterra", "kind": "organisation", "forms": ["Fonterra", "Fonterra Co-operative Group Ltd"]},
                    "e3": {"name": "Wellington", "kind": "place", "forms": ["Wellington"]},
                    "e4": {"name": "Hipkins", "kind": "person", "forms": ["Hipkins"]}},
       "quotes": [{"text": "x", "speaker": "e1"}], "roles": [{"who": "e1", "role": "leader", "of": "e2"}]}


def test_keys_are_the_registers_keys_and_one_word_is_no_person_key():
    assert news.keys_of("Chris Hipkins", "person", ["Hipkins"]) == ["chris hipkins"]
    org = news.keys_of("Fonterra", "organisation", ["Fonterra Co-operative Group Ltd"])
    assert org[0] == "fonterra" and len(org) == 2
    assert news.keys_of("Hipkins", "person", ["Hipkins"]) == []


def test_an_article_s_entities_carry_how_it_holds_them():
    es = {e["entity"]: e for e in news.entities_of(GOT, "Hipkins says Fonterra must pay")}
    assert set(es) == {"e1", "e2"}, "a place is not a register's; a one-word person has no key"
    assert es["e1"]["quoted"] and es["e1"]["in_role"] and es["e1"]["in_headline"] and es["e1"]["mentions"] == 2
    assert es["e2"]["in_role"] and not es["e2"]["quoted"] and es["e2"]["in_headline"]
