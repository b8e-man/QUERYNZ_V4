"""The text reader's call and its storage, on a fake server: the call names
the model, the answer is parsed and stored once under the reader's stamp,
a replay asks nothing, and a useless answer stores nothing. No model."""
import json
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


def test_an_answer_with_no_usable_object_stores_nothing_and_fails_the_piece():
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        with pytest.raises(RuntimeError):
            M.read_one(SHA, {1: "x"}, profile="courts-nzsc-judgment", version=2, url=URL, model="qwen4exp", store=store,
                       post=_server("I cannot read this.", []))
        assert M.stored(SHA, "courts-nzsc-judgment", 2, store) is None


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
