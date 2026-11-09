"""The keyword index's writer and reader (support/textindex), on a tiny index of invented texts built in a tmp folder.
The Papers Past lane's own tests (registers/papers_past/tests/test_papers_past_search.py) hold its behaviour through the
move; these hold the pieces the news index adds: a text key, folding, a phrase, and the move into place whole."""
import os

import pytest

from support.textindex import read, write

pytest.importorskip("tantivy")

SPEC = write.NEWS
DOCS = [
    {"ref": "news:t/1", "headline": "Māori land court sits", "text": "The Māori Land Court sat at Ōrewa on Tuesday.",
     "day": 20200301, "publisher": "Invented Herald"},
    {"ref": "news:t/2", "headline": "Maori Land Court adjourns", "text": "The maori land court adjourned.", "day": 20210301,
     "publisher": "Invented Post"},
    {"ref": "news:t/3", "headline": "Court news", "text": "land of the court", "day": None, "publisher": None},
]


@pytest.fixture(scope="module")
def ix(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("tx") / "news")
    made = write.build(iter(DOCS), path, SPEC, threads=1, heap=15_000_000)
    assert made["items"] == len(DOCS)
    return path


def test_fold_keeps_the_length_and_folds_macrons_and_case():
    for s in ("Māori Ōrewa", "Te Pāti Māori — ‘quoted’", "ÆON 12/3"):
        assert len(read.fold(s)) == len(s)
    assert read.fold("Māori, Ōrewa!") == "maori  orewa "


def test_folding_finds_each_spelling_both_ways(ix):
    assert sorted(read.phrase(ix, ["Maori"], ["headline", "text"])["keys"]) == ["news:t/1", "news:t/2"]
    assert sorted(read.phrase(ix, ["Māori"], ["headline", "text"])["keys"]) == ["news:t/1", "news:t/2"]
    assert read.phrase(ix, ["orewa"], ["text"])["keys"] == ["news:t/1"]


def test_a_phrase_is_its_words_together_in_order(ix):
    assert sorted(read.phrase(ix, ["land", "court"], ["text"])["keys"]) == ["news:t/1", "news:t/2"]
    assert read.phrase(ix, ["court", "land"], ["text"])["count"] == 0
    assert read.phrase(ix, [], ["text"])["count"] == 0


def test_a_query_with_filters_and_order(ix):
    assert read.have(ix, ints=("day",), exact=("publisher",)) == {"day", "publisher"}
    got = read.search(ix, "court", ["headline", "text"], key="ref", order_by="day", descending=True, folded=True)
    assert got["count"] == 3 and got["keys"][:2] == ["news:t/2", "news:t/1"] and got["keys"][2] == "news:t/3"
    assert read.search(ix, "court", ["text"], key="ref", terms=[("publisher", "Invented Post")])["keys"] == ["news:t/2"]
    assert read.search(ix, "court", ["text"], key="ref", ranges=[("day", 20200101, 20201231)])["keys"] == ["news:t/1"]
    assert read.search(ix, "Ōrewa", ["text"], key="ref", folded=True)["keys"] == ["news:t/1"]


def test_the_build_moves_into_place_whole(tmp_path):
    path = str(tmp_path / "ix")
    write.build(iter(DOCS[:1]), path, SPEC, threads=1, heap=15_000_000)
    write.build(iter(DOCS), path, SPEC, threads=1, heap=15_000_000)
    assert not os.path.exists(path + ".new") and not os.path.exists(path + ".old")
    read.forget(path)
    assert read.phrase(path, ["court"], ["headline", "text"])["count"] == 3


def test_a_missing_index_is_said():
    with pytest.raises(FileNotFoundError):
        read.phrase("/nonexistent/qv4-textindex-test", ["x"], ["text"])
