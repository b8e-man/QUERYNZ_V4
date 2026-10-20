"""The review agent (track C): the screen says only what the registers state
outright; the model's answer is held to the grammar and anything else is
contested; a web query carries a name and a public role at most and a
citation must have been fetched; the apply path refuses while the switch is
off or the judgment is unmeasured; the score's arithmetic and the pass mark."""
import json

import pytest

import links
from links import check, review


def _evidence(**shared):
    base = {"first_and_last_name": True, "full_name_with_middle": False, "middle_names_differ": False,
            "same_company_or_body": False, "registered_offices_shared": 0}
    return {"rows": [], "name": {}, "link": None, "watch_flags": [], "shared": {**base, **shared}}


def test_the_screen_decides_only_what_the_registers_state():
    assert review.screen(_evidence()) is None
    assert review.screen(_evidence(full_name_with_middle=True)) is None            # a matching middle name still goes to the model
    v = review.screen(_evidence(middle_names_differ=True))
    assert v["verdict"] == "not the same" and v["screen"] == "middle-names-differ"
    ev = _evidence()
    ev["link"] = {"link_id": 1, "rule": "source-identifier@1", "rule_evidence": {}}
    assert review.screen(ev)["verdict"] == "no reason to doubt"
    ev["link"]["rule"] = "name-and-address@1"
    assert review.screen(ev) is None


def test_the_three_verdicts_and_what_counts_as_a_split():
    assert review.VERDICTS == ("no reason to doubt", "contested", "not the same")
    assert review.SPLITS == ("contested", "not the same")
    assert review.PASS_MARK == {"wrongly_split_per_100": 1.0}
    assert links.SETTINGS["review_applies"] == "off"
    assert review.VERDICT_SCHEMA["properties"]["verdict"]["enum"] == list(review.VERDICTS)


def test_read_uses_the_screen_before_the_model_and_the_grammar_on_the_call():
    seen = {}

    def post(url, body, timeout):
        seen.update(body)
        return {"model": body["model"], "choices": [{"message": {"content": '{"verdict": "no reason to doubt", "reasoning": "same middle name, one office"}'}}]}

    v = review.read(_evidence(middle_names_differ=True), url="http://127.0.0.1:8111/v1/chat/completions", model="m", post=post)
    assert v["verdict"] == "not the same" and not seen
    v = review.read(_evidence(), url="http://127.0.0.1:8111/v1/chat/completions", model="m", post=post)
    assert v["verdict"] == "no reason to doubt" and v["screen"] == "model" and v["model"] == "m"
    assert seen["response_format"]["json_schema"]["schema"] == review.VERDICT_SCHEMA
    assert seen["max_tokens"] == review.MAX_TOKENS
    with pytest.raises(RuntimeError):
        review.read(_evidence())        # the model is needed and none was given


def test_the_fingerprint_covers_the_judgment_and_is_stable():
    assert review.fingerprint() == review.fingerprint() and len(review.fingerprint()) == 16
    old = review.SYSTEM
    try:
        review.SYSTEM = old + " "
        changed = review.fingerprint()
    finally:
        review.SYSTEM = old
    assert changed != review.fingerprint()      # a changed prompt is a new judgment, so a new measurement


def test_a_web_query_is_a_name_and_a_public_role_at_most_and_citations_must_be_fetched():
    assert review.web_query("Jane Example", "director") == "Jane Example director"
    with pytest.raises(ValueError):
        review.web_query("Jane Example", "12 Example Street")     # an address is never a query
    with pytest.raises(ValueError):
        review.web_query("")
    kept, dropped = review.cite_check(["https://a/x", "https://b/y"], {"https://a/x"})
    assert kept == ["https://a/x"] and dropped == ["https://b/y"]
    with pytest.raises(NotImplementedError):
        review.search("Jane Example director")


class _Conn:
    """A connection that answers scripted queries and refuses to write."""
    def __init__(self, answers):
        self.answers, self.writes = answers, []

    def execute(self, sql, params=None):
        for key, rows in self.answers.items():
            if key in sql:
                return _Cur(rows)
        if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            self.writes.append(sql)
            return _Cur([])
        return _Cur([])

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def commit(self):
        pass


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


def test_apply_refuses_while_the_switch_is_off_and_while_unmeasured(monkeypatch):
    conn = _Conn({})
    with pytest.raises(RuntimeError, match="off"):
        review.apply(conn, "links")
    monkeypatch.setitem(links.SETTINGS, "review_applies", "on")
    with pytest.raises(RuntimeError, match="not been measured"):
        review.apply(conn, "links")
    assert conn.writes == []


def test_apply_adds_a_decision_per_split_then_rebuilds_when_on_and_passed(monkeypatch):
    monkeypatch.setitem(links.SETTINGS, "review_applies", "on")
    conn = _Conn({"FROM links.scores": [("score-1", {"passed": True})],
                  "FROM links.readings r": [(9, "a:1", "b:2", "contested", "common name, nothing joining", "watched-1", {"rows": []}, [])]})
    rebuilt = []
    out = review.apply(conn, "links", log=lambda *a: None, rebuild=lambda c, s, log: rebuilt.append(s) or {"groups": 1})
    assert out["decisions_added"] == 1 and out["score_run"] == "score-1" and rebuilt == ["links"]
    assert any("INSERT INTO links.decisions" in w for w in conn.writes)


def test_the_check_fails_if_a_reading_became_a_decision_while_off():
    none = _Conn({"FROM links.decisions WHERE made_by LIKE": [(0,)], "FROM links.decisions d WHERE": [(0,)]})
    assert all(r["ok"] for r in check.check_review_switch(none, "links", applies=False))
    some = _Conn({"FROM links.decisions WHERE made_by LIKE": [(3,)], "FROM links.decisions d WHERE": [(0,)]})
    r = check.check_review_switch(some, "links", applies=False)
    assert r[0]["ok"] is False and r[0]["review_agent_decisions"] == 3 and r[1]["ok"] is True
    unscored = _Conn({"FROM links.decisions WHERE made_by LIKE": [(3,)], "FROM links.decisions d WHERE": [(3,)]})
    assert check.check_review_switch(unscored, "links", applies=True)[1]["ok"] is False


def test_the_report_counts_splits_by_truth_band_and_kind_and_applies_the_pass_mark():
    rows = (
        [("two-directors-one-company", "two people", "rare", "model", "contested", False)] * 60
        + [("two-directors-one-company", "two people", "rare", "model", "no reason to doubt", True)] * 40
        + [("member-and-candidacy", "one person", "rare", "source-identifier", "no reason to doubt", False)] * 99
        + [("member-and-candidacy", "one person", "rare", "model", "not the same", False)] * 1
    )
    conn = _Conn({"FROM links.readings WHERE run_id": rows})
    out = review.report(conn, "links", "score-t", model="m", log=lambda *a: None)
    assert out["pairs"] == 200
    assert out["one_person"]["all"] == {"pairs": 100, "not the same": 1, "contested": 0, "no reason to doubt": 99, "by the screen": 99,
                                        "split": 1, "split_per_100": 1.0}
    assert out["two_people"]["all"]["split_per_100"] == 60.0
    assert out["by_kind"]["two-directors-one-company"]["without_identical_full_name_and_middle"]["pairs"] == 60
    assert out["model_alone"]["one_person"]["pairs"] == 1
    assert out["passed"] is False          # 1 in 100 is not fewer than 1 in 100
    assert any("INSERT INTO links.scores" in w for w in conn.writes)
    assert json.dumps(out, default=str)


def test_two_roles_stand_at_once_when_their_filed_windows_overlap_and_an_open_end_stands_today():
    assert review._overlap({"from": "2020-01-01", "to": ""}, {"from": "2024-05-05", "to": ""})
    assert review._overlap({"from": "2020-01-01", "to": "2021-01-01"}, {"from": "2020-06-01", "to": ""})
    assert not review._overlap({"from": "2020-01-01", "to": "2021-01-01"}, {"from": "2022-01-01", "to": ""})
    assert review._overlap({"from": "", "to": ""}, {"from": "2022-01-01", "to": ""})
