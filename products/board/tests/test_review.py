"""The review tab (review.py): a set read from its file, one question drawn with its marks, answers only ever added."""
import json

from products.board import review

SET = {"title": "A set", "about": "", "articles": {"a1": {"title": "Head", "site": "x.nz", "date": "2026-11-01",
                                                        "body": "Jane Doe, chief executive of Acme, said <b>hi</b>."}},
       "questions": [
           {"id": "q1", "kind": "role", "label": "Job title", "article": "a1",
            "ask": [{"text": "Is "}, {"text": "Jane Doe", "mark": "who"}, {"text": " at "}, {"text": "Acme", "mark": "org"}],
            "context": [{"text": "Jane Doe", "mark": "who"}, {"text": ", chief executive of "}, {"text": "Acme", "mark": "org"}],
            "choices": [{"key": "yes", "label": "Yes"}, {"key": "no", "label": "No"}], "sides": {"gold": "yes", "model": "no"}},
           {"id": "q2", "kind": "quote", "label": "Who said it", "article": "a1", "ask": [{"text": "Said?"}],
            "context": [{"text": "said hi"}], "choices": [{"key": "yes", "label": "Yes"}], "sides": {"gold": "yes", "model": "yes"}}]}


def test_one_question_with_its_marks_and_no_sides(tmp_path, monkeypatch):
    (tmp_path / "s-1.json").write_text(json.dumps(SET))
    monkeypatch.setattr(review, "DIR", tmp_path)
    html = review.render_set("s-1", review.load("s-1"), {})
    assert '<mark class="who">Jane Doe</mark>' in html and '<mark class="org">Acme</mark>' in html
    assert 'data-key="1"' in html and "question 1 of 2" in html
    assert "&lt;b&gt;hi&lt;/b&gt;" in html and "<b>hi</b>" not in html       # the article's text is escaped
    assert "model" not in html.split("rv-card", 1)[1]                         # which side said what is never shown


def test_next_unanswered_and_the_tally(tmp_path, monkeypatch):
    (tmp_path / "s-1.json").write_text(json.dumps(SET))
    monkeypatch.setattr(review, "DIR", tmp_path)
    d = review.load("s-1")
    assert review.next_open(d["questions"], {"q1": {"choice": "yes"}})["id"] == "q2"
    assert review.next_open(d["questions"], {}, after="q1")["id"] == "q2"
    done = review.render_set("s-1", d, {"q1": {"choice": "yes", "note": ""}, "q2": {"choice": "yes", "note": ""}})
    assert "Every question in this set is answered" in done and "100%" in done


def test_take_refuses_an_unknown_choice_and_adds_a_known_one(tmp_path, monkeypatch):
    (tmp_path / "s-1.json").write_text(json.dumps(SET))
    monkeypatch.setattr(review, "DIR", tmp_path)
    got = []
    monkeypatch.setattr(review.state, "answer", lambda *a: got.append(a) or 1)
    try:
        review.take({"set": ["s-1"], "q": ["q1"], "choice": ["maybe"]})
        assert False
    except ValueError:
        pass
    assert review.take({"set": ["s-1"], "q": ["q1"], "choice": ["no"], "note": [" n "]}) == "/review?set=s-1&after=q1"
    assert got == [("s-1", "q1", "no", "n")]


def test_a_bad_set_name_reads_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "DIR", tmp_path)
    assert review.load("../etc/passwd") is None and review.load("") is None
