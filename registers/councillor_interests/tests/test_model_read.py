"""The register PDF's text reader (profile interests-register-pdf-text v1), on invented text and a fake server: the
profile recognises a register by its markers and turns away an appointments list, a scan and a non-PDF (pinned both
ways); whole pages are packed into pieces under the budget; nothing the lane never reads (real property, a home, an
address, a road, a contact, a spouse's or partner's interests) reaches a row or the stored reading, whatever the model
answers; the reading is stored once per piece and replayed; a missing piece makes the document wait. Every name,
company and place is invented. No model, no database."""
import json
import tempfile

import pytest

from support import reader as rd
from registers.councillor_interests import model_read as M

SHA = "c1" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"
REGISTER = {1: "INVENTED DISTRICT COUNCIL\nRegister of Members' Pecuniary Interests\nAs at 1 February 2026\n" + "x" * 200,
            2: "Mayor Tama Invented\nEmployment, trade or profession   Invented Farms\n" + "y" * 200}
APPOINTMENTS = {1: "Appointments made by Council to external organisations\nCr Example: Invented Trust Board\n" + "z" * 200}
SECRETS = ("14 Pretend Street", "State Highway 99, Imaginary", "RD 7 Nowhere", "Lot 9 DP 123456", "hemi@invented.example",
           "021 555 0199", "Valley View Road", "Aroha Madeup", "Spouse Employer Ltd", "Family home, Imaginary Valley")
ANSWER = json.dumps({"as_at": "1 February 2026", "members": [
    {"member": "Tama Invented", "role": "Mayor", "interests": [
        {"category": "Company directorships and controlling interests", "kind": "company",
         "entries": ["Invented Holdings Limited, Director", "Nil", "14 Pretend Street"]},
        {"category": "Has a beneficial interest", "kind": "real property",
         "entries": ["State Highway 99, Imaginary", "Family home, Imaginary Valley"]},
        {"category": "Interest in land", "kind": "other", "entries": ["Lot 9 DP 123456"]},
        {"category": "Spouse or partner interests", "kind": "employment", "entries": ["Aroha Madeup – Spouse Employer Ltd"]},
    ]},
    {"member": "Mere Madeup", "role": "Councillor", "interests": [
        {"category": "Trusts", "kind": "trust", "entries": ["Madeup Family Trust", "RD 7 Nowhere", "Valley View Road, Nowhere"]},
        {"category": "Organisations", "kind": "organisation",
         "entries": ["Rotary Club of Nowhere", "Contact: hemi@invented.example or 021 555 0199", "Aroha Madeup (wife), Invented Kindergarten Board"]},
        {"category": "Employment", "kind": "weird kind", "entries": []},
    ]},
    {"member": "", "interests": []}, "not a dict"]})


def _server(answers, calls: list):
    answers = list(answers)

    def post(url, body, timeout):
        calls.append(body)
        a = answers.pop(0) if len(answers) > 1 else answers[0]
        return {"model": body["model"], "choices": [{"message": {"content": a}}], "usage": {}}
    return post


@pytest.fixture
def pdf(monkeypatch):
    """A PDF whose text layer is `texts`, without a PDF: the text-layer helpers stand in."""
    state = {"texts": REGISTER, "how": "text"}
    monkeypatch.setattr(M.pages, "text_pages", lambda data, *a, **k: dict(state["texts"]))
    monkeypatch.setattr(M.pages, "read_from", lambda data, texts=None: state["how"])
    return state


def test_the_profile_is_proposed_with_its_reading_rule():
    from support import profiles
    p = profiles.profile(M.PROFILE, path=M.PROPOSED)
    assert p and p["version"] == M.profile_version() >= 1
    assert p["reading"]["budget_chars"] == M.BUDGET_CHARS and p["reading"]["split"] == M.SPLIT == "pages, then lines"
    assert p["tooling"]["read"] == "registers/councillor_interests/model_read.py"


def test_recognition_both_ways(pdf):
    assert M.recognise(b"%PDF-1.7 ...")[0] == ""
    pdf["texts"] = APPOINTMENTS
    assert M.recognise(b"%PDF-1.7 ...")[0] == M.NOT_A_REGISTER
    pdf["texts"], pdf["how"] = REGISTER, "pixels"
    assert M.recognise(b"%PDF-1.7 ...")[0] == M.WAIT_PAGES
    assert M.recognise(b"<html>pecuniary interests</html>")[0] == "not a PDF"
    for marker in ("Summary of pecuniary and other specified interests", "Register of Interests 2026",
                   "Declaration of interests", "section 54E(1)(a)", "Interests Register"):
        assert M.MARKERS.search(marker), marker
    for not_one in ("Appointments made by Council", "Code of conduct", "Elected members' remuneration"):
        assert not M.MARKERS.search(not_one), not_one


def test_whole_pages_are_packed_under_the_budget():
    texts = {1: "a" * 100, 2: "b" * 100, 3: "", 4: "c" * 100, 5: "d" * 500}
    parts, big, thin = M.pieces(texts, budget=260)
    assert [(f, l) for f, l, _ in parts] == [(1, 2), (4, 4)] and big == [5] and thin == [3]
    assert all(len(t) <= 260 + 40 for _f, _l, t in parts) and "[page 4]" in parts[1][2]


def test_nothing_the_lane_never_reads_reaches_a_row():
    parsed = M.parse_answer(ANSWER)
    assert [m["member"] for m in parsed["members"]] == ["Tama Invented", "Mere Madeup"]
    rows, withheld = M.kept(parsed["members"])
    assert [(r["member"], r["category"], r["kind"], r["entries"]) for r in rows] == [
        ("Tama Invented", "Company directorships and controlling interests", "company", ["Invented Holdings Limited, Director"]),
        ("Mere Madeup", "Trusts", "trust", ["Madeup Family Trust"]),
        ("Mere Madeup", "Organisations", "organisation", ["Rotary Club of Nowhere"]),
        ("Mere Madeup", "Employment", "other", [])]
    blob = repr(rows)
    assert not [s for s in SECRETS if s in blob]
    whys = {w for (_c, w) in withheld}
    assert any(w.startswith("real property") for w in whys) and any(w.startswith("a spouse") for w in whys)
    assert sum(withheld.values()) == 8


def test_read_once_per_piece_stored_clean_replayed_and_waiting(pdf):
    calls = []
    store = rd.Store(tempfile.mkdtemp())
    got = M.read_document(SHA, b"%PDF-1.7", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
    assert got["state"] == "read" and got["pieces"] == 1 and got["read"] == 1 and len(calls) == 1
    assert calls[0]["model"] == "qwen4exp" and calls[0]["temperature"] == 0.0 and "Mayor Tama Invented" in calls[0]["messages"][1]["content"]
    stored = store.get(M.key_for(SHA, 1, 1, "qwen4exp"))
    assert not [s for s in SECRETS if s in stored.text], "the stored reading holds nothing the lane never reads"
    again = M.read_document(SHA, b"%PDF-1.7", version=1, url=URL, model="qwen4exp", store=store, post=_server([ANSWER], calls))
    assert again["replayed"] == 1 and len(calls) == 1
    out = M.replay(SHA, b"%PDF-1.7", version=1, store=store, model="qwen4exp")
    assert out["state"] == "read" and out["as_at"] == "1 February 2026" and len(out["rows"]) == 4
    assert {r["pages"] for r in out["rows"]} == {"1-2"} and {r["model"] for r in out["rows"]} == {"qwen4exp"}
    assert M.replay("d2" * 32, b"%PDF-1.7", version=1, store=store, model="qwen4exp")["state"] == M.WAIT_TEXT


def test_a_useless_answer_is_asked_again_once_then_set_aside(pdf):
    calls = []
    store = rd.Store(tempfile.mkdtemp())
    got = M.read_document(SHA, b"%PDF-1.7", version=1, url=URL, model="qwen4exp", store=store,
                          post=_server(["no json here", "still none"], calls))
    assert len(calls) == M.ATTEMPTS and got["unusable"] == 1
    assert M.replay(SHA, b"%PDF-1.7", version=1, store=store, model="qwen4exp")["state"].startswith("set aside")


MUTANTS = {
    "real property kept": ('if c["kind"] in NEVER_KEPT or read.WITHHELD.search(cat):', 'if read.WITHHELD.search(cat):'),
    "roads kept": ("return read.withheld_entry(e) or bool(ROAD.search(e))", "return read.withheld_entry(e)"),
    "spouse entries kept": ("elif read.PRIVATE_PERSON.search(e):", "elif False:"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name, monkeypatch):
    import inspect
    import types
    a, b = MUTANTS[name]
    src = inspect.getsource(M)
    assert src.count(a) == 1, name
    mod = types.ModuleType("mutant_model_read")
    mod.__dict__["__file__"] = M.__file__
    exec(compile(src.replace(a, b), M.__file__, "exec"), mod.__dict__)
    with pytest.raises(AssertionError):
        rows, _w = mod.kept(mod.parse_answer(ANSWER)["members"])
        assert not [s for s in SECRETS if s in repr(rows)]


def test_the_page_profile_reads_a_printed_register_and_not_a_landing_page():
    """interests-register-html-text, both ways: a page that prints the register (long, naming it often, linking no
    register document) is read; a page that links a register PDF, or names it seldom, is not; a council with a
    register document held, or whose terms bar automated access, has no page read."""
    host, url = "www.invented.govt.nz", "https://www.invented.govt.nz/council/pecuniary-interests"
    body = ("<html><nav>menu pecuniary interests</nav><h1>Register of members' pecuniary interests</h1>"
            + "".join(f"<h2>Cr Member {i}</h2><p>Pecuniary interests (s 54E(1)(a)): Invented {i} Limited, Director</p>"
                      f"<p>Employment: Invented Farms</p>" + "<p>" + "w" * 120 + "</p>" for i in range(12))
            + "</html>").encode()
    state, texts, profile = M.recognise_page(body, url, host)
    assert state == "" and profile == M.PAGE_PROFILE and "Cr Member 11" in "\n".join(texts.values())
    assert "menu" not in "\n".join(texts.values()), "navigation is dropped"
    linked = body.replace(b"</h1>", b'</h1><a href="/files/register-of-pecuniary-interests.pdf">Register (PDF)</a>')
    assert M.recognise_page(linked, url, host)[0].startswith("a landing page")
    short = b"<html><p>See our register of pecuniary interests.</p></html>"
    assert M.recognise_page(short, url, host)[0].startswith("not a register page")
    assert M.page_wanted("Invented District Council", set())
    assert not M.page_wanted("Invented District Council", {"Invented District Council"})
    assert not M.page_wanted("Auckland Council", set())


def test_a_page_over_the_budget_is_cut_at_line_ends():
    texts = {1: "\n".join(f"line {i} " + "x" * 90 for i in range(40)), 2: "short page " * 10}
    parts, big, _thin = M.pieces(texts, budget=1000)
    assert not big and all(len(t) <= 1000 for _f, _l, t in parts)
    assert [f for f, _l, _t in parts].count(1) >= 4 and parts[-1][0] == 2
    assert "line 39" in "\n".join(t for f, _l, t in parts if f == 1)
