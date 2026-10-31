"""The text reader's call and its storage, on a fake server: each piece read
once and stored at its page, the pieces joined into one reading at page 1
under the `joined` settings, a replay asking nothing, an answer cut at the
token cap salvaged, an answer with no object asked once more and then stored
unusable, the call refused off the box. No model."""
import json
import tempfile

import pytest

from support import reader as rd
from registers.hansard import model_read as M, split as S
from registers.hansard.tests.test_hansard_split import final_text

SHA = "ab" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"


def _server(answers, calls: list):
    """answers: one string for every call, or a list taken in order."""
    def post(url, body, timeout):
        calls.append(body)
        a = answers if isinstance(answers, str) else answers[min(len(calls) - 1, len(answers) - 1)]
        return {"model": body["model"], "choices": [{"message": {"content": a}}],
                "usage": {"prompt_tokens": len(body["messages"][1]["content"]) // 4, "completion_tokens": 50}}
    return post


def _answer(*names, summary="A debate about a bill."):
    return json.dumps({"summary": summary,
                       "names": [{"name": n, "kind": "person", "role": "chief executive", "of": "Example Agency"} for n in names]})


def test_a_piece_is_read_once_stored_at_its_page_and_replayed_and_the_prompt_asks_for_names_not_speakers():
    calls = []
    d = S.split(final_text(), "2024-11-20")
    p = S.pieces_of(d, M.BUDGET)[2]
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_piece(SHA, p, profile="hansard-day", version=1, url=URL, model="qwen4exp", store=store,
                           post=_server(_answer("Sample Person"), calls))
        assert got["names"] == [{"name": "Sample Person", "kind": "person", "role": "chief executive", "of": "Example Agency"}]
        assert got["piece"] == p.number and got["section"] == 2 and not got["replayed"] and got["prompt_tokens"]
        assert calls[0]["model"] == "qwen4exp" and calls[0]["temperature"] == 0.0 and calls[0]["max_tokens"] == M.MAX_TOKENS
        assert calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
        assert calls[0]["messages"][0]["content"] == M.PROMPT and "Do not list the speakers themselves" in M.PROMPT
        assert calls[0]["messages"][1]["content"].endswith(p.text)
        again = M.read_piece(SHA, p, profile="hansard-day", version=1, url=URL, model="qwen4exp", store=store,
                             post=_server("{}", calls))
        assert again["replayed"] and len(calls) == 1, "a stored reading is never remade"
        assert store.has(M.piece_key(SHA, p.number, "hansard-day", 1, "qwen4exp"))
        assert not store.has(M.piece_key(SHA, p.number, "hansard-day", 2, "qwen4exp")), "another version is another reading"


def test_the_pieces_join_into_one_reading_at_page_one_that_the_load_picks_up():
    calls = []
    d = S.split(final_text(), "2024-11-20")
    pieces = S.pieces_of(d, M.BUDGET)
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = [M.read_piece(SHA, p, profile="hansard-day", version=1, url=URL, model="qwen4exp", store=store,
                            post=_server(_answer(f"Person {p.number}", f"Body {p.number}"), calls)) for p in pieces]
        joined = M.join(SHA, got, profile="hansard-day", version=1, model="qwen4exp", store=store)
        assert joined.page == 1 and joined.settings["joined"] and joined.checks["pieces"] == len(pieces)
        assert joined.checks["names"] == 2 * len(pieces) and joined.key == M.key_for(SHA, "hansard-day", 1, "qwen4exp")
        assert joined.key != M.piece_key(SHA, 1, "hansard-day", 1, "qwen4exp"), "piece 1 and the joined reading are two keys"
        stored = M.stored(SHA, "hansard-day", 1, store)
        assert [p["piece"] for p in stored["pieces"]] == [p.number for p in pieces]
        assert M.stored(SHA, "hansard-day", 2, store)["key"] == joined.key, "a later version replays the day read whole (1 November)"
        assert M.stored(SHA, "hansard-day", 2, store, model="other-model") is not None
        rows = M.people_rows(SHA, stored, {"key": "2024-11-20"}, "hansard-day", 1, "2026-10-31T10:00:00+13:00")
        assert len(rows) == 2 * len(pieces) and rows[0]["key"] == f"{SHA}/person/1" and rows[-1]["key"] == f"{SHA}/person/{2 * len(pieces)}"
        assert rows[0]["place"] == "text reader, piece 1, name 1" and rows[2]["place"] == "text reader, piece 2, name 3"
        assert rows[0]["section"] == f"2024-11-20/{pieces[0].section}" and rows[0]["of"] == "Example Agency"
        assert {r["read_from"] for r in rows} == {"text"} and {r["model"] for r in rows} == {"qwen4exp"}


def _cut_answer(n: int = 60) -> str:
    whole = _answer(*(f"Body {i} Limited" for i in range(n)))
    return whole[:whole.rfind("}", 0, whole.rfind("}") - 1) - 15]       # the token cap fell inside the last entry


def test_an_answer_cut_at_the_token_cap_keeps_its_complete_entries_and_says_so():
    cut = _cut_answer()
    parsed = M.parse_answer(cut)
    assert parsed["truncated"] and 55 <= len(parsed["names"]) <= 59 and parsed["summary"] == "A debate about a bill."
    assert all(n["name"].endswith("Limited") for n in parsed["names"]), "the cut entry is dropped, never a half name"
    assert M.parse_answer(_answer("A"))["truncated"] is False


def test_a_name_repeated_or_empty_or_a_bad_kind_is_folded_and_no_object_is_none():
    body = {"summary": "s", "names": [{"name": "Body One", "kind": "company"}, {"name": "body one", "kind": "COMPANY"},
                                      {"name": "Body One", "kind": "agency"}, {"name": " ", "kind": "person"},
                                      {"name": "X Y", "kind": "club"}, "not a dict"]}
    parsed = M.parse_answer(json.dumps(body))
    assert [(n["name"], n["kind"]) for n in parsed["names"]] == [("Body One", "company"), ("Body One", "agency"), ("X Y", "other")]
    assert M.parse_answer("no object here") is None and M.parse_answer('{"summary": "s"}') is None


def test_an_answer_with_no_usable_object_is_asked_once_more_on_half_the_piece_then_stored_unusable():
    calls = []
    d = S.split(final_text(), "2024-11-20")
    p = S.pieces_of(d, M.BUDGET)[2]
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_piece(SHA, p, profile="hansard-day", version=1, url=URL, model="qwen4exp", store=store,
                           post=_server("I cannot read this.", calls))
        assert len(calls) == M.ATTEMPTS == 2
        assert calls[1]["messages"][1]["content"].startswith("Answer with the one JSON object only")
        assert len(calls[1]["messages"][1]["content"]) < len(calls[0]["messages"][1]["content"])
        assert got["unusable"] == M.UNUSABLE % 2 and got["names"] == [] and not got["replayed"]
        again = M.read_piece(SHA, p, profile="hansard-day", version=1, url=URL, model="qwen4exp", store=store,
                             post=_server("{}", calls))
        assert again["replayed"] and again["unusable"] and len(calls) == 2, "an unusable reading is not asked again"
        joined = M.join(SHA, [got], profile="hansard-day", version=1, model="qwen4exp", store=store)
        assert joined.checks["unusable"] == 1


def test_the_whole_day_as_one_piece_of_the_job_reads_every_piece_and_joins_them(monkeypatch):
    calls = []
    rec = {"sitting_date": "2024-11-20", "text": final_text()}
    monkeypatch.setattr("support.docstore.landing.read_bytes", lambda sha: json.dumps(rec).encode())
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        line = M.piece(SHA, url=URL, model="qwen4exp", store=store, post=_server(_answer("Sample Person"), calls))
        n = len(S.packed(S.pieces_of(S.split(final_text(), "2024-11-20"), M.budget_of()), M.budget_of()))
        assert line["pieces"] == n == len(calls) and line["names"] == n and line["replayed"] == 0 and line["layout"] == "final"
        assert line["profile"] == f"hansard-day@{M.profile_version()}" and line["chars_per_token"]
        again = M.piece(SHA, url=URL, model="qwen4exp", store=store, post=_server("{}", calls))
        assert again["replayed"] == n and len(calls) == n, "the second run replays every piece and asks nothing"
        assert M.stored(SHA, "hansard-day", M.profile_version(), store)["checks"]["names"] == n


def test_a_text_the_profile_cannot_split_fails_the_piece_naming_why(monkeypatch):
    rec = {"sitting_date": "2024-11-20", "text": "no pages here"}
    monkeypatch.setattr("support.docstore.landing.read_bytes", lambda sha: json.dumps(rec).encode())
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(RuntimeError, match="cannot split"):
            M.piece(SHA, url=URL, model="qwen4exp", store=rd.Store(td), post=_server("{}", []))


def test_the_call_goes_to_a_local_address_only():
    from support import modelclient
    d = S.split(final_text(), "2024-11-20")
    p = S.pieces_of(d, M.BUDGET)[2]
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(modelclient.Refused):
            M.read_piece(SHA, p, profile="hansard-day", version=1, url="https://api.example.com/v1/chat/completions",
                         model="qwen4exp", store=rd.Store(td), post=_server("{}", []))


def test_the_budget_fits_the_profile_s_context():
    """40,000 characters at the measured 4.0 characters a token (the worst piece of the sample, 31 October 2026)
    is 10,000 tokens; with the prompt and the answer the request stays under the text-reader context of 16,384."""
    prompt_tokens = len(M.PROMPT) / 4
    assert M.BUDGET / 4.3 + prompt_tokens + M.MAX_TOKENS <= 32768
    assert M.budget_of() == M.BUDGET == M.settings()["budget_chars"]


def test_whole_sections_pack_into_one_request_and_a_name_keeps_its_section():
    """31 October 2026, for speed: consecutive whole sections share one request within the budget, each marked
    [SECTION n]; the reader's "section" puts the name on its own section, and a section number the piece does
    not hold falls back to the piece's first section."""
    d = S.split(final_text(), "2024-11-20")
    whole = S.pieces_of(d, M.BUDGET)
    packed = S.packed(whole, M.BUDGET)
    assert len(whole) > 1 and len(packed) < len(whole)
    p = packed[0]
    assert p.sections == len(p.ids) > 1 and all(S.MARK.format(i) in p.text for i in p.ids) and p.chars <= M.BUDGET
    tiny = S.packed(whole, max(q.chars for q in whole) + 20)
    assert all(q.chars <= max(x.chars for x in whole) + 20 for q in tiny) and len(tiny) >= len(packed)
    ans = json.dumps({"summary": "s", "names": [{"name": "Ann Bee", "kind": "person", "section": p.ids[1]},
                                                  {"name": "Ann Bee", "kind": "person", "section": p.ids[0]},
                                                  {"name": "Cee Dee", "kind": "person", "section": 999}]})
    parsed = M.parse_answer(ans)
    assert len(parsed["names"]) == 3, "a name once in each section that names it"
    reading = {"pieces": [{"piece": 1, "section": p.section, "ids": list(p.ids), "names": parsed["names"]}],
               "reader": "r", "model": "m"}
    rows = M.people_rows(SHA, reading, {"key": "2024-11-20"}, "hansard-day", 2, "now")
    assert [r["section"] for r in rows] == [f"2024-11-20/{p.ids[1]}", f"2024-11-20/{p.ids[0]}", f"2024-11-20/{p.section}"]


def test_a_day_read_whole_under_an_earlier_version_is_replayed_not_read_again(tmp_path):
    """Arthur, 1 November 2026: the readings already made are kept; hansard-day 2 only packed the requests."""
    store = rd.Store(str(tmp_path))
    sha = "ab" * 32
    piece_reading = rd.Reading(sha, 1, M.READER, "qwen4exp", {"piece": 1}, "hansard-day", 1, "text", '{"people": []}')
    joined = rd.Reading(sha, 1, M.READER, "qwen4exp", {"joined": True}, "hansard-day", 1, "text",
                        json.dumps({"pieces": [{"number": 1, "section": 1, "names": [{"name": "Jane Doe"}]}]}),
                        checks={"names": 1})
    store.put(piece_reading)
    store.put(joined)
    got = M.stored(sha, "hansard-day", 2, store)
    assert got is not None and got["pieces"][0]["names"][0]["name"] == "Jane Doe" and got["key"] == joined.key
    assert M.stored("cd" * 32, "hansard-day", 2, store) is None
