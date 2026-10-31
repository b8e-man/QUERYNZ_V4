"""The text reader's call and its storage, on a fake server: the call names
the model, the answer is parsed and stored once under the reader's stamp,
a replay asks nothing, a document over its profile's budget is read in
pieces whose readings are stored one by one and joined under the one hash
(a name once across pieces, the summary from the parts' summaries in one
more call), an answer cut at the token cap is salvaged to its complete
entries, and an answer with no object is asked once more and then stored
unusable (nothing raises, nothing loops). No model."""
import json
import re
import tempfile

import pytest

from support import reader as rd
from registers.courts import model_read as M
from registers.courts import pieces as PC

SHA = "12" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"
NZSC = "courts-nzsc-judgment"
RULE = {"budget_chars": 34000, "split": "paragraphs"}


def _server(answer: str, calls: list):
    def post(url, body, timeout):
        calls.append(body)
        return {"model": body["model"], "choices": [{"message": {"content": answer}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    return post


def _answering(by_part: dict, calls: list):
    """A server whose answer depends on the part asked for (the user message names it), and on the summary prompt."""
    def post(url, body, timeout):
        calls.append(body)
        system, user = body["messages"][0]["content"], body["messages"][1]["content"]
        if system == M.SUMMARY_PROMPT:
            answer = json.dumps({"summary": "The whole document, summarised from its parts."})
        else:
            m = re.search(r"part (\d+) of (\d+)", user)
            answer = by_part[int(m.group(1)) if m else 1]
        return {"model": body["model"], "choices": [{"message": {"content": answer}}]}
    return post


def _judgment(paragraphs: int, chars_each: int = 1200) -> dict:
    """An invented judgment: a caption page and numbered paragraphs, several a page."""
    caption = "IN THE SUPREME COURT OF NEW ZEALAND\n" + " " * 60 + "[2099] NZSC 7\n" + " " * 15 + "BETWEEN" + " " * 20 + "EXAMPLE HOLDINGS LIMITED\n" \
        + " " * 44 + "Appellant\nHearing:   1 June 2099\nCounsel:   P Q Rowe KC for Appellant\nJudgment:  2 June 2099\n\n     JUDGMENT OF THE COURT\n"
    pages, page, n = {1: caption}, 2, 1
    while n <= paragraphs:
        body = ""
        for _ in range(6):
            if n > paragraphs:
                break
            body += f"[{n}]  " + ("Words of paragraph %d. " % n) * (chars_each // 22) + "\n\n"
            n += 1
        pages[page] = body
        page += 1
    return pages


def test_one_reading_per_document_stored_under_the_model_the_prompt_and_the_rule_and_replayed():
    calls = []
    answer = json.dumps({"summary": "A judgment about a deposit.", "people": [{"name": "Sample Person", "kind": "person", "role": "party", "role_text": "respondent"}]})
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, {1: "IN THE SUPREME COURT", 2: "text"}, profile=NZSC, version=3, url=URL, model="qwen4exp",
                         store=store, post=_server(answer, calls))
        assert got["summary"] == "A judgment about a deposit." and got["people"][0]["name"] == "Sample Person" and not got["replayed"]
        assert got["pieces"] == 1 and got["calls"] == 1
        assert calls[0]["model"] == "qwen4exp" and calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
        assert calls[0]["messages"][0]["content"] == M.PROMPT and "IN THE SUPREME COURT" in calls[0]["messages"][1]["content"]
        assert "[page 1]" in calls[0]["messages"][1]["content"] and "part 1 of" not in calls[0]["messages"][1]["content"], "one piece: no part lead"
        again = M.read_one(SHA, {1: "other text"}, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_server("{}", calls))
        assert again["replayed"] and len(calls) == 1, "a stored reading is never remade"
        stored = M.stored(SHA, NZSC, 3, store)
        rule = PC.rule_of(NZSC)
        assert stored["model"] == "qwen4exp" and stored["reader"] == M.READER and stored["key"].endswith(rd.settings_hash(M.settings(rule)))
        assert M.stored(SHA, NZSC, 2, store) is None, "another profile version is another reading"
        s = M.settings(rule)
        assert s["budget_chars"] == rule["budget_chars"] and s["split"] == rule["split"] and "head_chars" not in s, "the rule is in the key; no excerpt"


def test_a_document_over_the_budget_is_read_in_pieces_joined_under_the_one_hash():
    texts = _judgment(120)                      # about 150,000 characters: five pieces at 34,000
    parts, why = PC.plan(texts, RULE)
    assert parts and len(parts) >= 4 and why is None
    n = len(parts)
    by_part = {i: json.dumps({"summary": f"Part {i} summary.", "people": [
        {"name": "Sample Person", "kind": "person", "role": "party", "role_text": "appellant"},
        {"name": f"Witness {i}", "kind": "person", "role": "witness", "role_text": "witness"},
        {"name": "Able CJ", "kind": "person", "role": "judge"}]}) for i in range(1, n + 1)}
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, texts, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_answering(by_part, calls), rule=RULE)
        assert got["pieces"] == n and got["calls"] == n, "one call a piece; no summary is joined (1 November 2026)"
        assert got["summary"] == "Part 1 summary.", "a part that still answers a summary: the first is kept"
        names = [(p["name"], p["role"]) for p in got["people"]]
        assert names.count(("Sample Person", "party")) == 1 and names.count(("Able CJ", "judge")) == 1, "a name once across pieces"
        assert [p["name"] for p in got["people"] if p["role"] == "witness"] == [f"Witness {i}" for i in range(1, n + 1)]
        assert got["people"][0]["part"] == 1 and got["people"][-1]["part"] == n
        for i, body in enumerate(calls[:n], 1):
            user = body["messages"][1]["content"]
            assert len(user) < RULE["budget_chars"] + 2000, "every piece within the budget"
            assert f"part {i} of {n}" in user, "every piece is told which it is"
            if i == 1:
                assert "IN THE SUPREME COURT" in user and "[1]  Words" in user and "[…]" not in user, "the caption first, whole"
            else:
                assert "[…]" in user and "IN THE SUPREME COURT" in user, "a later piece opens with the document's first lines"
        assert len(calls) == n, "no call to join summaries"
        # every piece's reading is stored on its own, so a stopped job resumes: a second run makes no call
        for i in range(1, n + 1):
            assert store.has(M.piece_key(SHA, NZSC, 3, "qwen4exp", RULE, i, n))
        again = M.read_one(SHA, texts, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_server("{}", calls), rule=RULE)
        assert again["replayed"] and len(calls) == n
        rows = M.people_rows(SHA, M.stored(SHA, NZSC, 3, store, rule=RULE), {"citation": "[2099] NZSC 7"}, NZSC, 3, "now")
        assert rows[0]["place"] == f"text reader, part 1 of {n}, name 1" and rows[-1]["place"].startswith(f"text reader, part {n} of {n}")


def test_a_job_stopped_between_pieces_resumes_at_the_next_piece():
    texts = _judgment(120)
    parts, _ = PC.plan(texts, RULE)
    n = len(parts)
    by_part = {i: json.dumps({"summary": f"S{i}", "people": [{"name": f"Body {i} Limited", "kind": "body", "role": "company"}]}) for i in range(1, n + 1)}
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        # the first two pieces were read before the deadline stopped the job
        for i in (1, 2):
            M._read_piece(SHA, parts[i - 1], i, n, profile=NZSC, version=3, rule=RULE, url=URL, model="qwen4exp", store=store,
                          post=_answering(by_part, calls), request=None)
        assert len(calls) == 2
        got = M.read_one(SHA, texts, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_answering(by_part, calls), rule=RULE)
        assert got["calls"] == n - 2 and got["pieces_replayed"] == 2 and len(got["people"]) == n


def test_an_answer_with_no_usable_object_is_asked_once_more_then_stored_unusable_and_the_piece_ends():
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, {1: "x" * 20000}, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store,
                         post=_server("I cannot read this.", calls))
        assert len(calls) == M.ATTEMPTS == 2, "one more shape of retry, never a loop"
        assert calls[1]["messages"][1]["content"].startswith("Answer with the one JSON object only")
        assert got["unusable"] == M.UNUSABLE % 2 and got["people"] == [] and got["summary"] is None and not got["replayed"]
        stored = M.stored(SHA, NZSC, 3, store)
        assert stored["unusable"] == M.UNUSABLE % 2, "the load sees the reason and sets the document aside"
        again = M.read_one(SHA, {1: "x"}, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_server("{}", calls))
        assert again["replayed"] and again["unusable"] and len(calls) == 2, "an unusable reading is not asked again"


def test_one_unusable_piece_among_several_leaves_the_others_readings_standing():
    texts = _judgment(120)
    parts, _ = PC.plan(texts, RULE)
    n = len(parts)
    by_part = {i: json.dumps({"summary": f"S{i}", "people": [{"name": f"Body {i} Limited", "kind": "body", "role": "company"}]}) for i in range(1, n + 1)}
    by_part[2] = "no object here"
    calls = []
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        got = M.read_one(SHA, texts, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_answering(by_part, calls), rule=RULE)
        assert got["calls"] == n + 1, "piece 2 asked twice; no summary call"
        assert len(got["people"]) == n - 1 and not got["unusable"]
        assert json.loads(store.get(M.key_for(SHA, NZSC, 3, "qwen4exp", RULE)).text)["parts_unusable"] == 1


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
        got = M.read_one(SHA, {1: "x"}, profile=NZSC, version=3, url=URL, model="qwen4exp", store=store, post=_server(cut, calls))
        assert len(calls) == 1 and got["truncated"] and len(got["people"]) >= 85 and not got["unusable"]
        assert M.stored(SHA, NZSC, 3, store)["truncated"]


def test_a_name_the_model_repeats_is_listed_once():
    people = [{"name": "Body One Limited", "kind": "body", "role": "company"}] * 3 + [{"name": "body one limited", "kind": "body", "role": "party"}]
    parsed = M.parse_answer(json.dumps({"summary": "s", "people": people}))
    assert [p["role"] for p in parsed["people"]] == ["company", "party"]
    assert M.parse_answer("no object here") is None and M.parse_answer('{"summary": "s"}') is None


def test_the_call_goes_to_a_local_address_only():
    from support import modelclient
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(modelclient.Refused):
            M.read_one(SHA, {1: "x"}, profile=NZSC, version=3, url="https://api.example.com/v1/chat/completions",
                       model="qwen4exp", store=rd.Store(td), post=_server("{}", []))


def test_a_document_the_rule_cannot_split_never_reaches_the_model():
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError, match="cannot read it"):
            M.read_one(SHA, {1: "x" * 40000}, profile="courts-media-release", version=2, url=URL, model="qwen4exp", store=rd.Store(td),
                       post=lambda *a, **k: pytest.fail("the model was called"))


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
