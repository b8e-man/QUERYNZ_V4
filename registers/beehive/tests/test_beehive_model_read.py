"""The text reader's call and its storage, on a fake server: the call names
the model and carries the title and body, the answer is parsed and
normalised, stored once under the reader's stamp and replayed; a useless
answer is asked for again once and then stored as set aside with the
reason (never raised, never asked again); a record with no body is set
aside without a call. No model, no database."""
import json
import tempfile

import pytest

from support import reader as rd
from registers.beehive import model_read as M

SHA = "34" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"
BODY = ("Finance Minister Example Person today announced funding for Example Trust, chaired by Sample Chair. "
        "The grant is administered by the Ministry of Example. Example Holdings Limited will build the Wellington site. ") * 2
ANSWER = json.dumps({"summary": "A funding announcement for a trust and a building site.",
                     "people": [{"name": "Example Person", "kind": "person", "role": "Minister", "role_text": "Finance Minister", "of": None},
                                {"name": "Example Trust", "kind": "organisation", "role": "recipient", "role_text": "recipient of funding", "of": "x"},
                                {"name": "Sample Chair", "kind": "person", "role": "chairperson", "role_text": "chair of Example Trust", "of": "Example Trust"},
                                {"name": "Ministry of Example", "kind": "agency", "role": "organisation"},
                                {"name": "Example Holdings Limited", "kind": "company", "role": "builder"},
                                {"name": "Wellington", "kind": "place-not-a-person", "role": "mentioned"},
                                {"name": "Example Person", "kind": "person", "role": "minister"},
                                {"name": "", "kind": "person", "role": "other"}, "not a dict"]})


def _server(answers, calls: list):
    answers = list(answers)

    def post(url, body, timeout):
        calls.append(body)
        a = answers.pop(0) if len(answers) > 1 else answers[0]
        return {"model": body["model"], "choices": [{"message": {"content": a}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    return post


def test_the_profile_is_proposed_and_versioned():
    assert M.profile_version() >= 1
    assert M.settings()["attempts"] == M.ATTEMPTS and M.settings()["temperature"] == 0.0


def test_one_reading_per_document_stored_under_the_model_and_the_prompt_and_replayed():
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, "Funding for Example Trust", BODY, version=1, url=URL, model="qwen4exp", store=store,
                         post=_server([ANSWER], calls))
        assert got["usable"] and not got["replayed"] and got["summary"].startswith("A funding announcement")
        assert calls[0]["model"] == "qwen4exp" and calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
        assert calls[0]["temperature"] == 0.0 and calls[0]["messages"][0]["content"] == M.PROMPT
        user = calls[0]["messages"][1]["content"]
        assert user.startswith("TITLE: Funding for Example Trust\n\nBODY:\nFinance Minister")
        again = M.read_one(SHA, "other", "other text " * 30, version=1, url=URL, model="qwen4exp", store=store,
                           post=_server(["{}"], calls))
        assert again["replayed"] and len(calls) == 1, "a stored reading is never remade"
        s = M.stored(SHA, 1, store)
        assert s["model"] == "qwen4exp" and s["reader"] == M.READER and s["profile"] == M.PROFILE and s["profile_version"] == 1
        assert s["key"].endswith(rd.settings_hash(M.settings())) and len(s["people"]) == 6
        assert M.stored(SHA, 2, store) is None, "another profile version is another reading"
        assert M.stored_under_other_versions(SHA, 2, store) == [1] and M.stored_under_other_versions(SHA, 1, store) == []


def test_the_answer_is_normalised_to_the_kinds_and_roles_and_a_name_listed_twice_is_one():
    p = M.parse_answer("Here you are:\n" + ANSWER + "\nDone.")
    rows = {(r["name"], r["kind"]): r for r in p["people"]}
    assert len(p["people"]) == 6 and set(rows) == {("Example Person", "person"), ("Example Trust", "body"), ("Sample Chair", "person"),
                                                   ("Ministry of Example", "agency"), ("Example Holdings Limited", "company"),
                                                   ("Wellington", "place")}
    assert rows[("Example Person", "person")]["role"] == "minister" and rows[("Example Person", "person")]["role_text"] == "Finance Minister"
    assert rows[("Sample Chair", "person")]["role"] == "chair" and rows[("Sample Chair", "person")]["of"] == "Example Trust"
    assert rows[("Example Trust", "body")]["role"] == "recipient" and rows[("Example Trust", "body")]["of"] is None, "`of` is a person's"
    assert rows[("Example Holdings Limited", "company")]["role"] == "other", "a role outside the list is other"
    assert rows[("Wellington", "place")]["role"] == "mentioned"
    assert M.parse_answer("I cannot read this.") is None and M.parse_answer('{"summary": "x"}') is None
    assert M.parse_answer('{"people": [], "summary": ""}') == {"summary": None, "people": []}


def test_a_useless_answer_is_asked_again_once_then_set_aside_with_the_reason_and_never_asked_again():
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, "t", BODY, version=1, url=URL, model="qwen4exp", store=store, post=_server(["No.", "Still no."], calls))
        assert len(calls) == 2 and calls[1]["messages"][-1]["content"] == M.NUDGE and calls[1]["messages"][-2]["role"] == "assistant"
        assert not got["usable"] and got["people"] == [] and got["summary"] is None and "after 2 attempt" in got["reason"]
        s = M.stored(SHA, 1, store)
        assert s is not None and not s["usable"] and s["reason"] == got["reason"]
        again = M.read_one(SHA, "t", BODY, version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
        assert again["replayed"] and not again["usable"] and len(calls) == 2, "set aside is a reading: never asked again"
        good = M.read_one("56" * 32, "t", BODY, version=1, url=URL, model="qwen4exp", store=store, post=_server(["No.", ANSWER], calls))
        assert good["usable"] and len(calls) == 4, "the second attempt may answer"


def test_a_record_with_no_body_or_a_tiny_one_is_set_aside_without_a_call():
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, "t", "", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
        assert not got["usable"] and got["reason"] == "no body" and calls == []
        tiny = M.read_one("78" * 32, "t", "only a few words here", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
        assert not tiny["usable"] and tiny["reason"].startswith("body under 20 words") and calls == []
    assert M.recognise_body({"id": "x", "url": "https://www.beehive.govt.nz/release/x", "body_text": "a b"}).startswith("body under")
    assert M.recognise_body({"id": "x", "url": "https://www.beehive.govt.nz/release/x"}) == "no body"
    assert M.recognise_body({"id": "x", "url": "https://example.test/x", "body_text": BODY}) == "its url is not a beehive.govt.nz page"
    assert M.recognise_body({"id": "x", "url": "https://www.beehive.govt.nz/release/x", "body_text": BODY}) == ""


def test_a_long_body_is_cut_to_its_head_and_tail():
    long = "word " * 20000
    ex = M.excerpt(None, long)
    assert ex.startswith("BODY:\nword") and "[… text omitted …]" in ex and len(ex) < M.HEAD_CHARS + M.TAIL_CHARS + 100
    assert M.excerpt("A title", "short body") == "TITLE: A title\n\nBODY:\nshort body"


def test_the_call_goes_to_a_local_address_only():
    from support import modelclient
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(modelclient.Refused):
            M.read_one(SHA, "t", BODY, version=1, url="https://api.example.com/v1/chat/completions", model="qwen4exp",
                       store=rd.Store(td), post=_server([ANSWER], []))


def test_people_rows_keep_the_row_contract_and_cite_the_release():
    from support import rowcontract
    reading = {"people": M.parse_answer(ANSWER)["people"], "reader": M.READER, "model": "qwen4exp", "profile": M.PROFILE,
               "profile_version": 1}
    rows = M.people_rows(SHA, reading, {"key": "https://www.beehive.govt.nz/release/x", "published_on": "2025-03-04", "type": "release"},
                         "2026-10-31T10:00:00+13:00")
    assert [r["key"] for r in rows] == [f"{SHA}/person/{n}" for n in range(1, 7)]
    assert all(rowcontract.validate(r) == [] for r in rows) and all(r["place"] == f"text reader, name {n}" for n, r in enumerate(rows, 1))
    assert rows[0]["release"] == "https://www.beehive.govt.nz/release/x" and rows[0]["model"] == "qwen4exp" and rows[0]["type"] == "release"
