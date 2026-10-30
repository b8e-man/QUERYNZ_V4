"""The text reader's call and its storage, on a fake server: the call names
the model, the answer is parsed and stored once under the reader's stamp,
a replay asks nothing, an answer cut at the token cap is salvaged to its
complete entries, and an answer with no object is asked once more and then
stored unusable (nothing raises, nothing loops). No model."""
import json
import re
import tempfile

import pytest

from support import reader as rd
from registers.courts import model_read as M

SHA = "12" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"


def _server(answer: str, calls: list):
    def post(url, body, timeout):
        calls.append(body)
        return {"model": body["model"], "choices": [{"message": {"content": answer}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    return post


def test_one_reading_per_document_stored_under_the_model_and_the_prompt_and_replayed():
    calls = []
    answer = json.dumps({"summary": "A judgment about a deposit.", "people": [{"name": "Sample Person", "kind": "person", "role": "party", "role_text": "respondent"}]})
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, {1: "IN THE SUPREME COURT", 2: "text"}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp",
                         store=store, post=_server(answer, calls))
        assert got["summary"] == "A judgment about a deposit." and got["people"][0]["name"] == "Sample Person" and not got["replayed"]
        assert calls[0]["model"] == "qwen4exp" and calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
        assert calls[0]["messages"][0]["content"] == M.PROMPT and "IN THE SUPREME COURT" in calls[0]["messages"][1]["content"]
        again = M.read_one(SHA, {1: "other text"}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp", store=store,
                           post=_server("{}", calls))
        assert again["replayed"] and len(calls) == 1, "a stored reading is never remade"
        stored = M.stored(SHA, "courts-nzsc-judgment", 2, store)
        assert stored["model"] == "qwen4exp" and stored["reader"] == M.READER and stored["key"].endswith(M.settings.__call__()["prompt_sha"][:0] + rd.settings_hash(M.settings()))
        assert M.stored(SHA, "courts-nzsc-judgment", 1, store) is None, "another profile version is another reading"


def test_an_answer_with_no_usable_object_is_asked_once_more_then_stored_unusable_and_the_piece_ends():
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, {1: "x" * 40000}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp", store=store,
                         post=_server("I cannot read this.", calls))
        assert len(calls) == M.ATTEMPTS == 2, "one more shape of retry, never a loop"
        assert len(calls[1]["messages"][1]["content"]) < len(calls[0]["messages"][1]["content"]), "the retry sends a shorter excerpt"
        assert calls[1]["messages"][1]["content"].startswith("Answer with the one JSON object only")
        assert got["unusable"] == M.UNUSABLE % 2 and got["people"] == [] and got["summary"] is None and not got["replayed"]
        stored = M.stored(SHA, "courts-nzsc-judgment", 2, store)
        assert stored["unusable"] == M.UNUSABLE % 2, "the load sees the reason and sets the document aside"
        again = M.read_one(SHA, {1: "x"}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp", store=store,
                           post=_server("{}", calls))
        assert again["replayed"] and again["unusable"] and len(calls) == 2, "an unusable reading is not asked again"


def _cut_answer(n: int = 90) -> str:
    people = [{"name": f"Body {i} Limited", "kind": "body", "role": "company", "role_text": "respondent", "for": None} for i in range(n)]
    whole = json.dumps({"summary": "A judgment naming many bodies.", "people": people})
    return whole[:whole.rfind("}", 0, whole.rfind("}") - 1) - 20]       # the token cap fell inside the last entry


def test_an_answer_cut_at_the_token_cap_keeps_its_complete_entries_and_says_so():
    cut = _cut_answer(90)
    with pytest.raises(ValueError):
        json.loads(M._JSON.search(cut).group(0))        # the whole answer is not an object: the cap fell inside an entry
    parsed = M.parse_answer(cut)
    assert parsed["truncated"] and parsed["summary"] == "A judgment naming many bodies."
    assert 85 <= len(parsed["people"]) <= 89 and parsed["people"][0]["name"] == "Body 0 Limited"
    assert all(p["name"].endswith("Limited") for p in parsed["people"]), "the cut entry is dropped, never a half name"
    whole = M.parse_answer(json.dumps({"summary": "s", "people": [{"name": "A B", "kind": "person", "role": "party"}]}))
    assert whole["truncated"] is False
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, {1: "x"}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp", store=store,
                         post=_server(cut, calls))
        assert len(calls) == 1 and got["truncated"] and len(got["people"]) >= 85 and not got["unusable"]
        assert M.stored(SHA, "courts-nzsc-judgment", 2, store)["truncated"]


def test_a_name_the_model_repeats_is_listed_once():
    people = [{"name": "Body One Limited", "kind": "body", "role": "company"}] * 3 + [{"name": "body one limited", "kind": "body", "role": "party"}]
    parsed = M.parse_answer(json.dumps({"summary": "s", "people": people}))
    assert [p["role"] for p in parsed["people"]] == ["company", "party"]
    assert M.parse_answer("no object here") is None and M.parse_answer('{"summary": "s"}') is None


def test_the_call_goes_to_a_local_address_only():
    from support import modelclient
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(modelclient.Refused):
            M.read_one(SHA, {1: "x"}, profile="courts-nzsc-judgment", version=2, url="https://api.example.com/v1/chat/completions",
                       model="qwen4exp", store=rd.Store(td), post=_server("{}", []))


def test_kept_under_suppression_keeps_the_court_s_officers_and_the_crown_only():
    assert M.kept_under_suppression({"role": "judge", "name": "Able CJ"})
    assert M.kept_under_suppression({"role": "counsel", "name": "P Q Rowe KC"})
    assert M.kept_under_suppression({"role": "agency", "name": "Ministry of Example"})
    assert M.kept_under_suppression({"role": "party", "name": "The King"})
    assert M.kept_under_suppression({"role": "party", "name": "Attorney-General"})
    assert not M.kept_under_suppression({"role": "party", "name": "Sample Person"})
    assert not M.kept_under_suppression({"role": "witness", "name": "A Witness"})
    assert not M.kept_under_suppression({"role": "company", "name": "Example Holdings Limited"})
    assert not M.kept_under_suppression({"role": "party", "name": "Riverside Holdings Limited"}), "R is the Crown only on its own"
    assert M.kept_under_suppression({"role": "party", "name": "The Attorney-General of New Zealand"})
    assert not M.kept_under_suppression({"role": "other", "name": "Attorney-Generals Road Trust"})


def test_the_keep_rule_is_one_rule_for_the_load_and_the_sql_of_the_check_and_the_lever():
    from registers.courts import caption
    sql = M.kept_sql("n.")
    assert sql.startswith("(n.role IN (") and f"upper(n.name) ~ '{caption.CROWN.pattern}'" in sql and "%" not in sql
    assert all(f"'{r}'" in sql for r in M.KEPT_ROLES) and M.KEPT_ROLES == ("judge", "counsel", "agency")
    # the pattern is written in the regex both dialects share: no \b (a backspace to Postgres), no \d, no \s, no flags
    for escape in ("\\b", "\\d", "\\s", "\\w", "(?i)", "(?P<"):
        assert escape not in caption.CROWN.pattern, escape
    assert caption.CROWN.flags & ~re.U == 0
