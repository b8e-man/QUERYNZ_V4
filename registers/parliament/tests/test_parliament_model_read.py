"""The text reader's call and its storage, on a fake server (no model): the
budget and the split rule, several documents in one request keyed back,
one reading per document under the reader's stamp, a replay that asks
nothing, an answer cut at the token cap salvaged, a missing document asked
once more alone and then stored unusable (nothing raises, nothing loops),
and the call refused for any address that is not local. Then, on the
filled sample, every landed document of each profile held to its budget or
its split rule."""
import json
import os
import tempfile

import pytest

from support import reader as rd
from support import sample
from registers.parliament import model_read as M

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://127.0.0.1:8060/v1/chat/completions"
A, B, C = "a1" * 32, "b2" * 32, "c3" * 32
# sample.list: an archived "page" that is a WAV audio file's bytes served as text (a RIFF header, 22,496 NULs, 46,917
# characters, one sentence end): no boundary inside the budget, so the profile cannot split it
NOT_PROSE = "c90a270e810201d7f40e7f053b0146ab825d38c6df25f7f198afaee8f7f65db6"


def _answer(**docs) -> str:
    return json.dumps({"documents": [{"key": k, **v} for k, v in docs.items()]})


def _server(answers, calls: list):
    """answers: a string for every call, a list taken in order, or a dict by the piece number in the header
    ("part p of n"; the pieces of a split document are asked several at a time)."""
    import threading
    lock = threading.Lock()

    def post(url, body, timeout):
        with lock:
            calls.append(body)
            if isinstance(answers, dict):
                part = body["messages"][1]["content"].split(", part ")[1].split(" of ")[0]
                text = answers[int(part)]
            else:
                text = answers.pop(0) if isinstance(answers, list) else answers
        return {"model": body["model"], "choices": [{"message": {"content": text}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    return post


def _keys(body) -> list:
    user = body["messages"][1]["content"]
    return [line.split("]")[0][len("[document "):] for line in user.split("\n") if line.startswith("[document ")]


# ── the budget and the split rule ─────────────────────────────────────────────────────────────────────────────

def test_the_profiles_carry_the_budget_and_the_split_rule_at_version_2():
    for slug in (M.WAYBACK, M.WQ):
        p = M.profile_of(slug)
        assert int(p["version"]) >= 2 and M.budget(slug) == 24000
        assert "speaker turn" in p["config"]["split"] and "sentence" in p["config"]["split"]
        assert p["signals"]["text_chars_max" if slug == M.WAYBACK else "question_plus_reply_chars_max"] > 24000
    assert M.budget(M.WAYBACK) + 1000 < 32000, "the courts reader's excerpt is the ceiling to beat, not to copy"


def test_a_text_within_the_budget_goes_whole_and_one_over_it_is_cut_at_a_turn_then_a_paragraph_then_a_sentence():
    assert M.pieces_of("short text.", 100) == ["short text."]
    assert M.pieces_of("", 100) == [""]
    turn = "Hon SAMPLE MEMBER (Sample—Place): " + "words of a speech go on. " * 6
    text = ("Opening remarks of the day go on and on. " * 4) + turn + turn
    pieces = M.pieces_of(text, len(text) - 40)
    assert len(pieces) == 2 and pieces[1].startswith("Hon SAMPLE MEMBER (") and all(len(p) <= len(text) - 40 for p in pieces)
    para = ("First paragraph sentence one. Sentence two.\nSecond paragraph sentence. " * 6)
    pieces = M.pieces_of(para, 120)
    assert all(len(p) <= 120 for p in pieces) and all(not p.startswith(" ") for p in pieces)
    assert all(p.endswith(".") for p in pieces[:-1]), "a paragraph end is where a line ends"
    prose = "A sentence of prose that runs along. " * 40
    pieces = M.pieces_of(prose, 200)
    assert all(len(p) <= 200 for p in pieces) and all(p.endswith(".") for p in pieces[:-1])
    assert " ".join(pieces).split() == prose.split(), "nothing is dropped and nothing is excerpted"


def test_a_text_with_no_boundary_inside_the_budget_cannot_be_split_and_says_so():
    with pytest.raises(M.CannotSplit) as e:
        M.pieces_of("x" * 500, 100)
    assert "cannot split" in str(e.value) and "100 characters" in str(e.value)
    with pytest.raises(M.CannotSplit):
        M.pieces_of("word " * 100, 100)                 # spaces are not boundaries: a sentence end is


def test_the_cut_falls_past_a_third_of_the_window_never_at_its_start():
    text = "A. " + "B" * 150 + ". " + "C" * 150 + ". " + "D" * 50 + "."
    pieces = M.pieces_of(text, 200)
    assert len(pieces[0]) > 66, pieces[0][:20]


def test_the_question_and_the_reply_are_what_the_model_reads_never_the_provider_s_text():
    rec = {"questionText": " What? ", "replyText": "This.", "text": "provider run"}
    assert M.document_text(M.WQ, rec) == "QUESTION: What?\nREPLY: This."
    row = {"question_text": "Q", "reply_text": None}
    assert M.document_text(M.WQ, row) == "QUESTION: Q\nREPLY: "
    assert M.document_text(M.WAYBACK, {"text": " page text ", "html_title": "t"}) == "page text"


# ── the answer ────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_answer_is_keyed_back_and_each_name_listed_once_with_kind_and_role_closed():
    parsed = M.parse_answer("Here you are:\n" + _answer(
        d1={"summary": "A debate.", "people": [
            {"name": "Sample Person", "kind": "person", "role": "member", "role_text": "MP for Sample", "of": "Sample Party"},
            {"name": "sample person", "kind": "person", "role": "member"},
            {"name": "Example Agency", "kind": "agency", "role": "weird", "of": None},
            {"name": "", "kind": "person", "role": "member"}]},
        d2={"summary": "s", "people": []}))
    assert set(parsed) == {"d1", "d2"} and not parsed["d1"]["truncated"]
    assert [p["name"] for p in parsed["d1"]["people"]] == ["Sample Person", "Example Agency"]
    assert parsed["d1"]["people"][0]["of"] == "Sample Party" and parsed["d1"]["people"][0]["role_text"] == "MP for Sample"
    assert parsed["d1"]["people"][1]["role"] == "other" and parsed["d1"]["people"][1]["of"] is None
    assert parsed["d2"]["people"] == [] and parsed["d2"]["summary"] == "s"
    assert M.parse_answer("no object") is None and M.parse_answer('{"people": []}') is None
    assert M.parse_answer(json.dumps({"documents": [{"key": "d1", "people": [{"name": "X", "role": "minister"}]}]}))["d1"]["people"][0]["kind"] == "person"


def _cut_batch(n_docs: int = 3, n_people: int = 40) -> str:
    docs = {f"d{i}": {"summary": f"Document {i}.", "people": [
        {"name": f"Body {i}-{j} Limited", "kind": "company", "role": "other", "role_text": None, "of": None}
        for j in range(n_people)]} for i in range(1, n_docs + 1)}
    whole = _answer(**docs)
    second = whole.index('"key": "d2"')
    return whole[:second + 900]                          # the token cap fell inside document 2's people


def test_an_answer_cut_at_the_token_cap_keeps_the_complete_entries_marks_the_cut_document_and_drops_the_rest():
    cut = _cut_batch()
    with pytest.raises(ValueError):
        json.loads(M._JSON.search(cut).group(0))
    parsed = M.parse_answer(cut)
    assert set(parsed) == {"d1", "d2"}, "document 3 was after the cut"
    assert not parsed["d1"]["truncated"] and len(parsed["d1"]["people"]) == 40
    assert parsed["d2"]["truncated"] and 0 < len(parsed["d2"]["people"]) < 40
    assert all(p["name"].endswith("Limited") for p in parsed["d2"]["people"]), "never a half name"


# ── the call and the store ────────────────────────────────────────────────────────────────────────────────────

def test_several_documents_in_one_request_are_each_stored_once_under_their_own_hash_and_replayed():
    calls = []
    answer = _answer(d1={"summary": "One.", "people": [{"name": "Sample Person", "kind": "person", "role": "member"}]},
                     d2={"summary": "Two.", "people": [{"name": "Example Trust", "kind": "body", "role": "submitter"}]})
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_batch([(A, "QUESTION: a\nREPLY: b"), (B, "QUESTION: c\nREPLY: d")], profile=M.WQ, version=2,
                           url=URL, model="qwen4exp", store=store, post=_server(answer, calls))
        assert len(calls) == 1 and calls[0]["model"] == "qwen4exp" and calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
        assert calls[0]["temperature"] == 0.0 and calls[0]["max_tokens"] == M.MAX_TOKENS
        assert calls[0]["messages"][0]["content"] == M.PROMPT and _keys(calls[0]) == ["d1", "d2"]
        assert "QUESTION: a" in calls[0]["messages"][1]["content"] and "DOCUMENTS: 2" in calls[0]["messages"][1]["content"]
        assert got[A]["people"][0]["name"] == "Sample Person" and got[B]["summary"] == "Two." and not got[A]["replayed"]
        assert got[A]["people"][0]["piece"] == 1 and got[A]["pieces"] == 1 and got[A]["batch"] == 2
        one = M.stored(A, M.WQ, 2, store)
        assert one["model"] == "qwen4exp" and one["reader"] == M.READER and one["key"] == M.key_for(A, M.WQ, 2, "qwen4exp")
        assert M.stored(A, M.WQ, 1, store) is None, "another profile version is another reading"
        # alone or with others, the key is one: a single document is a batch of one
        again = M.read_batch([(A, "x"), (C, "QUESTION: e\nREPLY: f")], profile=M.WQ, version=2, url=URL, model="qwen4exp",
                             store=store, post=_server(_answer(d1={"summary": "Three.", "people": []}), calls))
        assert again[A]["replayed"] and again[A]["summary"] == "One." and not again[C]["replayed"]
        assert len(calls) == 2 and _keys(calls[1]) == ["d1"], "only the document without a reading was sent"


def test_a_document_the_answer_misses_is_asked_once_more_alone_then_stored_unusable_and_nothing_loops():
    calls = []
    answers = [_answer(d1={"summary": "One.", "people": []}),      # the batch: d2 missing
               "I cannot read this."]                               # d2 alone, the object only: nothing
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_batch([(A, "a"), (B, "b")], profile=M.WQ, version=2, url=URL, model="qwen4exp", store=store,
                           post=_server(answers, calls))
        assert len(calls) == 2 and _keys(calls[1]) == ["d2"]
        assert calls[1]["messages"][1]["content"].startswith("Answer with the one JSON object only")
        assert got[A]["unusable"] is None and got[B]["unusable"] == M.UNUSABLE % 2 and got[B]["people"] == []
        assert M.stored(B, M.WQ, 2, store)["unusable"], "the load sees the reason and sets the document aside"
        more = M.read_batch([(B, "b")], profile=M.WQ, version=2, url=URL, model="qwen4exp", store=store,
                            post=_server("{}", calls))
        assert more[B]["replayed"] and more[B]["unusable"] and len(calls) == 2, "an unusable reading is not asked again"


def test_a_document_over_the_budget_is_read_in_pieces_and_joined_under_the_one_hash():
    calls = []
    text = ("A sentence of the debate goes here. " * 30)
    pieces = M.pieces_of(text, 300)
    assert len(pieces) >= 3
    answers = {i: _answer(d1={"summary": f"Part {i}.", "people": [{"name": f"Person {i}", "kind": "person", "role": "member"}]})
               for i in range(1, len(pieces) + 1)}
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_split(A, pieces, profile=M.WAYBACK, version=2, url=URL, model="qwen4exp", store=store,
                           post=_server(answers, calls))
        assert len(calls) == len(pieces)
        assert any("part 1 of %d" % len(pieces) in c["messages"][1]["content"] for c in calls)
        assert got["pieces"] == len(pieces) and got["summary"] == "Part 1."
        assert [p["piece"] for p in got["people"]] == list(range(1, len(pieces) + 1))
        rows = M.people_rows(A, got, {"source_table": "wayback_pages", "source_key": "k", "dated": None,
                                      "citation_url": None}, M.WAYBACK, 2, "2026-10-31T10:00:00+13:00")
        assert rows[1]["place"] == "text reader, piece 2, name 2" and rows[0]["key"] == f"{A}/person/1"
        assert M.stored(A, M.WAYBACK, 2, store)["pieces"] == len(pieces)
        again = M.read_split(A, pieces, profile=M.WAYBACK, version=2, url=URL, model="qwen4exp", store=store,
                             post=_server("{}", calls))
        assert again["replayed"] and len(calls) == len(pieces)


def test_a_piece_answered_with_nothing_twice_makes_the_whole_document_unusable_naming_the_piece():
    calls = []
    pieces = ["First piece sentence.", "Second piece sentence."]
    answers = {1: _answer(d1={"summary": "One.", "people": []}), 2: "nothing"}
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_split(A, pieces, profile=M.WAYBACK, version=2, url=URL, model="qwen4exp", store=store,
                           post=_server(answers, calls))
        assert len(calls) == 3 and got["unusable"].endswith("(piece 2 of 2)") and got["people"] == []


def test_the_call_goes_to_a_local_address_only():
    from support import modelclient
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(modelclient.Refused):
            M.read_batch([(A, "a")], profile=M.WQ, version=2, url="https://api.example.com/v1/chat/completions",
                         model="qwen4exp", store=rd.Store(td), post=_server("{}", []))


def test_a_piece_s_text_is_the_request_s_only_text_and_the_header_names_the_kind_not_the_minister():
    """The asker and the Minister are the row's own columns: the user message carries the question and reply
    and the document's kind, nothing else; the settings carry the prompt's hash and the budget, so a changed
    prompt or budget is a new reading."""
    calls = []
    with tempfile.TemporaryDirectory() as td:
        M.read_batch([(A, "QUESTION: q\nREPLY: r")], profile=M.WQ, version=2, url=URL, model="qwen4exp",
                     store=rd.Store(td), post=_server(_answer(d1={"summary": "s", "people": []}), calls))
    user = calls[0]["messages"][1]["content"]
    assert user == "DOCUMENTS: 1\n\n[document d1] " + M.HEADER[M.WQ] + "\nQUESTION: q\nREPLY: r"
    s = M.settings(M.WQ)
    assert set(s) == {"prompt_sha", "budget_chars", "temperature", "max_tokens", "thinking"} and s["temperature"] == 0.0
    assert M.key_for(A, M.WQ, 2) != M.key_for(A, M.WAYBACK, 2)


# ── every landed document of the profile, to its budget or its split rule ─────────────────────────────────────

def test_every_sample_document_of_each_profile_is_within_the_budget_or_splits_by_the_rule():
    """The profile test the common rules ask for: the sample's real documents (hashes in sample.list; the long
    ones among them) are read from the store and held to the budget or the split rule; a document the rule
    cannot split would fail here by hash."""
    from support.docstore.landing import path_for, read_bytes
    items = [i for i in sample.read_list(os.path.join(LANE, "sample.list")) if not i.startswith("key:")]
    if not all(os.path.exists(path_for(s)) for s in items):
        pytest.skip("the sample's documents are not in this box's document store")
    seen = {M.WAYBACK: 0, M.WQ: 0}
    longest = {M.WAYBACK: (0, 0), M.WQ: (0, 0)}
    unsplit = set()
    for sha in items:
        rec = json.loads(read_bytes(sha))
        profile = M._profile_of_record(rec)
        if profile is None:
            continue
        text = M.document_text(profile, rec)
        try:
            pieces = M.pieces_of(text, M.budget(profile))
        except M.CannotSplit:
            unsplit.add(sha)
            continue
        assert all(len(p) <= M.budget(profile) for p in pieces), sha
        seen[profile] += 1
        longest[profile] = max(longest[profile], (len(text), len(pieces)))
    assert unsplit == {NOT_PROSE}, "the one document the rule cannot split is the WAV file served as a page; the load sets it aside at read"
    assert seen[M.WAYBACK] >= 10 and seen[M.WQ] >= 30, seen
    assert longest[M.WAYBACK][1] >= 20 and longest[M.WQ][1] == 2, (longest, "the sample holds the largest page and the longest question")


def test_a_busy_server_is_waited_for_and_asked_again_never_a_failed_read():
    import urllib.error
    calls = []
    answer = _answer(d1={"summary": "s", "people": []})

    def post(url, body, timeout):
        calls.append(body)
        if len(calls) < 3:
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, None)
        return {"model": body["model"], "choices": [{"message": {"content": answer}}], "usage": {}}
    parsed, served = M.ask([("d1", M.HEADER[M.WQ], "QUESTION: q\nREPLY: r")], url=URL, model="qwen4exp", post=post, sleep=0)
    assert len(calls) == 3 and "d1" in parsed and served == "qwen4exp"

    def refused(url, body, timeout):
        raise urllib.error.HTTPError(url, 500, "Server Error", {}, None)
    with pytest.raises(urllib.error.HTTPError):
        M.ask([("d1", "h", "t")], url=URL, model="qwen4exp", post=refused, sleep=0)
    calls.clear()

    def loading(url, body, timeout):
        calls.append(body)
        if len(calls) < 2:
            raise urllib.error.URLError(ConnectionResetError(104, "Connection reset by peer"))
        return {"model": body["model"], "choices": [{"message": {"content": answer}}], "usage": {}}
    parsed, _ = M.ask([("d1", "h", "t")], url=URL, model="qwen4exp", post=loading, sleep=0)
    assert len(calls) == 2 and "d1" in parsed, "a server loading is waited for"
