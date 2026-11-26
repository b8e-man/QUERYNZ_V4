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


def test_an_article_read_before_reader_6_takes_the_subjects_pass_alone_stored_and_recorded():
    import contextlib
    import json as J
    from support import reader as rd

    class Store:
        def __init__(self):
            self.put_ = []

        def has(self, k):
            return False

        def get(self, k):
            return rd.Reading(document="a" * 64, page=1, reader="registers.news.read 5", model="m", settings={},
                              profile="news-article", profile_version=1, read_from="text",
                              text=J.dumps({"entities": {"e1": {"name": "Police", "kind": "organisation"}}}))

        def put(self, r):
            self.put_.append(r)

    sql = []

    class C:
        def execute(self, q, p=None):
            sql.append((q, p))
            return type("R", (), {"fetchone": lambda _s: ("Guns seized", "A Writer", "Police found 3D-printed guns.", "k/old")})()

        def commit(self):
            pass

    @contextlib.contextmanager
    def connect():
        yield C()
    seen = {}

    def call(text, ents, url, model, lane=""):
        seen["ents"] = ents
        return {"subjects": [{"name": "3D printing", "kind": "technology", "words": "3D-printed", "inferred": False}], "dropped": []}
    st = Store()
    line = S.piece("rnz.co.nz/a", connect=connect, url="u", model="qwen38-27b", store=st, call=call)
    assert line.endswith("1 subjects kept, 0 dropped") and seen["ents"] == {"e1": {"name": "Police", "kind": "organisation"}}
    assert st.put_[0].reader == S.READER and J.loads(st.put_[0].text)["subjects"][0]["name"] == "3D printing"
    assert "INSERT INTO news_private.subjects_done" in sql[-1][0] and sql[-1][1][2:4] == (1, 0)
