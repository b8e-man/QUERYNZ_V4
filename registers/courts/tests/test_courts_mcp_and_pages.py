"""Two changes of 3 November 2026 (Arthur). The MCP's courts records carry `doc_date` (the judgment's own date; their
`date` is the arrival) and `citation`: where the document's reading has none the MCP's stands in, its basis marked;
where both exist the document's reading wins and the check counts the agreements. And a document no split rule fits
is read page by page: the profile's fallback, a new version whose reading version leaves every other reading keyed
as it was. Invented values only; no model, no database."""
import datetime as dt
import json
import tempfile

import pytest

from support import profiles as pr
from support import reader as rd
from registers.courts import capture, caption, check
from registers.courts import load as L
from registers.courts import model_read as M
from registers.courts import pieces as PC
from registers.courts import read as R

RULE = {"budget_chars": 34000, "split": "paragraphs"}
FALLING = {**RULE, "fallback": "pages"}
SHA = "34" * 32
URL = "http://127.0.0.1:8060/v1/chat/completions"


def _unnumbered(pages: int = 6, per_page: int = 9000) -> dict:
    """A determination whose text layer numbers no paragraph: over the budget, every page within it."""
    out = {1: "IN THE EMPLOYMENT RELATIONS AUTHORITY\nAUCKLAND\n[2099] NZERA 1\nBETWEEN  EXAMPLE LIMITED\nDETERMINATION OF THE AUTHORITY\n"}
    for p in range(2, pages + 2):
        out[p] = (f"Page {p} of the reasons, unnumbered. " * (per_page // 36))[:per_page]
    return out


def _numbered(paragraphs: int = 120) -> dict:
    pages, n, p = {1: "IN THE SUPREME COURT OF NEW ZEALAND\n[2099] NZSC 7\nJUDGMENT OF THE COURT\n"}, 1, 2
    while n <= paragraphs:
        pages[p] = "".join(f"[{k}]  " + f"Paragraph {k} says things. " * 50 + "\n\n" for k in range(n, min(n + 6, paragraphs + 1)))
        n += 6
        p += 1
    return pages


# ── the fallback ─────────────────────────────────────────────────────────────────────────────────────────────
def test_a_document_with_no_numbered_paragraphs_is_read_in_runs_of_whole_pages_by_the_fallback():
    texts = _unnumbered()
    assert PC.plan(texts, RULE)[0] is None, "the paragraph rule alone cannot split it (the set-aside of 31 October)"
    parts, why, used = PC.plan_how(texts, FALLING)
    assert why is None and used == "pages" and len(parts) >= 2
    assert all(len(p) <= RULE["budget_chars"] for p in parts)
    for p in sorted(texts):
        holders = [x for x in parts if f"[page {p}]\n" in x]
        assert len(holders) == 1, f"page {p} is in exactly one piece"
        assert texts[p].rstrip() in holders[0], f"page {p} is whole"
    assert parts[1].startswith(f"[part 2 of {len(parts)} of the document") and "IN THE EMPLOYMENT RELATIONS AUTHORITY" in parts[1]
    assert PC.count(texts, FALLING) == len(parts)


def test_a_document_the_rule_s_own_split_cuts_is_planned_exactly_as_before():
    texts = _numbered()
    before, _ = PC.plan(texts, RULE)
    parts, why, used = PC.plan_how(texts, FALLING)
    assert parts == before and used == "paragraphs" and len(parts) >= 3
    short = {1: "IN THE SUPREME COURT OF NEW ZEALAND\n[1] One.\n"}
    assert PC.plan_how(short, FALLING) == ([PC.body_of(short)], None, "paragraphs"), "a document that fits is the rule's own"


def test_a_page_over_the_budget_is_never_cut_and_the_document_stays_set_aside_named():
    texts = {1: "IN THE EMPLOYMENT RELATIONS AUTHORITY\n", 2: "x" * 40000, 3: "y" * 1000}
    parts, why, used = PC.plan_how(texts, FALLING)
    assert parts is None and used is None
    assert "fewer than two numbered paragraphs" in why and "the fallback by pages: a page of 40,0" in why


def test_a_fallback_is_pages_on_a_paragraph_or_numbered_rule_only():
    prof = lambda rule: (lambda s: {"reading": rule})  # noqa: E731
    assert PC.rule_of("x", profile_of=prof({**FALLING, "measured": "…"})) == FALLING
    with pytest.raises(LookupError):
        PC.rule_of("x", profile_of=prof({**RULE, "fallback": "halves"}))
    with pytest.raises(LookupError):
        PC.rule_of("x", profile_of=prof({"budget_chars": 34000, "split": "whole", "fallback": "pages"}))


def test_every_paragraph_and_numbered_profile_carries_the_page_fallback():
    for slug in sorted(R.TEXT_READ_SLUGS):
        rule = PC.rule_of(slug)
        assert rule.get("fallback") == ("pages" if rule["split"] in PC.FALLS_BACK else None), slug


# ── the reading's version and key ────────────────────────────────────────────────────────────────────────────
def test_the_fallback_versions_leave_every_stored_reading_keyed_as_before(tmp_path):
    p = str(tmp_path / "profiles.jsonl")
    pr.add_version("courts-test", {"title": "t", "prompt": "a", "reading": RULE}, by="t", path=p)
    pr.add_version("courts-test", {"title": "t", "prompt": "a", "reading": {**FALLING, "fallback_note": "why"}}, by="t", path=p)
    assert pr.reading_version("courts-test", p) == 1, "a reading the rule's own split made keeps its version"
    assert pr.reading_version("courts-test", p, fallback=True) == 2, "a reading the fallback made is the new version's"
    pr.add_version("courts-test", {"title": "t", "prompt": "b", "reading": FALLING}, by="t", path=p)
    assert pr.reading_version("courts-test", p) == pr.reading_version("courts-test", p, fallback=True) == 3


def test_the_ledger_s_courts_profiles_key_the_fallback_reading_by_its_own_version_and_the_rest_as_before():
    era = R.ERA
    assert R.profile_version(era) == 1, "every stored determination reading stands"
    # the version that brought the fallback in (a later version that changes no reading, such as the extract list's
    # next iteration, keeps it)
    assert R.profile_version(era, fallback=True) == pr.reading_version(era, fallback=True) > R.profile_version(era)
    _, _, version, used = R.text_reading(era, _unnumbered())
    assert (version, used) == (R.profile_version(era, fallback=True), "pages")
    _, _, version, used = R.text_reading(era, _numbered())
    assert (version, used) == (1, "paragraphs")


def test_a_reading_the_rule_s_own_split_made_keeps_its_key_and_the_fallback_s_reading_is_keyed_apart():
    assert M.settings(FALLING) == M.settings(RULE) == M.settings(FALLING, used="paragraphs")
    assert M.key_for(SHA, R.ERA, 1, "qwen4exp", FALLING, "paragraphs") == M.key_for(SHA, R.ERA, 1, "qwen4exp", RULE)
    assert M.settings(FALLING, used="pages")["fallback"] == "pages"
    assert M.key_for(SHA, R.ERA, 3, "qwen4exp", FALLING, "pages") != M.key_for(SHA, R.ERA, 3, "qwen4exp", FALLING)


def test_the_text_reader_reads_a_fallback_document_in_page_pieces_and_the_load_replays_it():
    calls = []

    def post(url, body, timeout):
        calls.append(body)
        if body["messages"][0]["content"] == M.SUMMARY_PROMPT:
            return {"model": body["model"], "choices": [{"message": {"content": json.dumps({"summary": "A determination."})}}]}
        answer = {"summary": "Part.", "people": [{"name": "Sample Member", "kind": "person", "role": "judge"}]}
        return {"model": body["model"], "choices": [{"message": {"content": json.dumps(answer)}}]}
    texts = _unnumbered()
    with tempfile.TemporaryDirectory() as td:
        store = rd.Store(td)
        with pytest.raises(ValueError):
            M.read_one(SHA, texts, profile=R.ERA, version=1, url=URL, model="qwen4exp", store=store, post=post, rule=RULE)
        got = M.read_one(SHA, texts, profile=R.ERA, version=3, url=URL, model="qwen4exp", store=store, post=post, rule=FALLING)
        n = len(PC.plan_how(texts, FALLING)[0])
        assert got["pieces"] == n >= 2 and got["calls"] == n + 1 and len(got["people"]) == 1
        reading = store.get(M.key_for(SHA, R.ERA, 3, "qwen4exp", FALLING, "pages"))
        assert reading.settings["fallback"] == "pages" and reading.profile_version == 3
        assert M.stored(SHA, R.ERA, 3, store, rule=FALLING, used="pages")["summary"] == "A determination."
        assert M.stored(SHA, R.ERA, 3, store, rule=FALLING) is None, "the load must ask under the split that cut it"


# ── the MCP's date and citation ──────────────────────────────────────────────────────────────────────────────
def test_the_entry_carries_the_mcp_record_s_citation_and_doc_date_never_its_arrival_date():
    rec = {"kind": "judgment_pdf", "citation": " [2099] NZHC 12 ", "doc_date": "2099-03-10", "date": "2099-11-03"}
    e = capture.entry("courts/1", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1, rec=rec)
    assert (e["mcp_citation"], e["mcp_doc_date"]) == ("[2099] NZHC 12", "2099-03-10")
    e = capture.entry("courts/2", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1, rec={"date": "2099-11-03"})
    assert (e["mcp_citation"], e["mcp_doc_date"]) == (None, None), "the record's `date` is the arrival, never the judgment's"


def test_the_mcp_record_s_court_and_its_reclassification_stamp_reach_the_documents_table():
    """The provider's `court_reclassified_at` (4 November 2026: it re-filed records under another court) and the
    `court` it re-filed them under, each in a documents column (ruling 96: their fields in our registers)."""
    rec = {"kind": "judgment_pdf", "court": "nzhc", "court_reclassified_at": "2026-11-03T21:14:05+00:00"}
    e = capture.entry("courts/1", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1, rec=rec)
    assert (e["mcp_court"], e["mcp_court_reclassified_at"]) == ("nzhc", "2026-11-03T21:14:05+00:00")
    e2 = capture.entry("courts/2", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1,
                       rec={"court_reclassified_at": "not a time"})
    assert (e2["mcp_court"], e2["mcp_court_reclassified_at"]) == (None, None)
    for col in ("mcp_court", "mcp_court_reclassified_at"):
        assert col in L.COLUMNS["documents"]
    res = R.read([e], data_of=lambda sha: None, store=None)
    assert (res.documents[0]["mcp_court"], res.documents[0]["mcp_court_reclassified_at"]) == \
        ("nzhc", "2026-11-03T21:14:05+00:00")


def test_mcp_date_takes_an_iso_day_in_a_possible_year_and_nothing_else():
    assert R.mcp_date("2099-03-10") == dt.date(2099, 3, 10)
    assert R.mcp_date("2025-04-17T00:00:00Z") == dt.date(2025, 4, 17)
    assert [R.mcp_date(v) for v in (None, "", "10 March 2025", "3023-10-17", "2025-02-30")] == [None] * 5


def test_the_mcp_fills_only_what_the_document_lacks_and_says_so():
    mcp = {"mcp_doc_date": dt.date(2099, 3, 10), "mcp_citation": "[2099] NZHC 12"}
    j = caption.Judgment()
    R.from_mcp(j, mcp)
    assert (j.judgment_date, j.date_basis, j.citation, j.citation_basis) == (dt.date(2099, 3, 10), R.MCP_DATE_BASIS,
                                                                             "[2099] NZHC 12", R.MCP_CITATION_BASIS)
    j = caption.Judgment(citation="[2099] NZHC 13", judgment_date=dt.date(2099, 3, 9), date_basis="label")
    R.from_mcp(j, mcp)
    assert (j.judgment_date, j.date_basis, j.citation, j.citation_basis) == (dt.date(2099, 3, 9), "label", "[2099] NZHC 13", "document"), \
        "the document's own reading wins where both exist"
    j = caption.Judgment()
    R.from_mcp(j, {"mcp_doc_date": None, "mcp_citation": None})
    assert (j.judgment_date, j.date_basis, j.citation, j.citation_basis) == (None, None, None, None)


class _Conn:
    """The two counts and the joined rows `check.mcp_agreement` asks for."""
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, args=None):
        rows = self.rows
        class _R:   # noqa: N801
            def fetchall(self):
                return rows

            def fetchone(self):
                col = 1 if "mcp_doc_date IS NOT NULL" in sql and "mcp_citation IS NOT NULL" not in sql else 2
                return (sum(1 for r in rows if r[col] is not None),)
        return _R()


def test_the_check_counts_agreements_disagreements_and_fills_with_keys_never_names():
    d = dt.date
    rows = [("courts/1", d(2099, 1, 1), "[2099] NZHC 1", d(2099, 1, 1), "label", "[2099]  NZHC 1", "document"),
            ("courts/2", d(2099, 1, 2), "[2099] NZHC 2", d(2099, 1, 3), "label", "[2099] NZHC 22", "document"),
            ("courts/3", d(2099, 1, 4), "[2099] NZHC 4", d(2099, 1, 4), R.MCP_DATE_BASIS, "[2099] NZHC 4", R.MCP_CITATION_BASIS),
            ("courts/4", None, "[2099] NZHC 5", None, None, "[2099] NZHC 5", "document")]
    out, keys = check.mcp_agreement(_Conn(rows), lambda t: t)
    assert out == {"records carrying doc_date": 3, "date agrees": 1, "date disagrees": 1, "date filled from the MCP": 1,
                   "records carrying citation": 4, "citation agrees": 2, "citation disagrees": 1, "citation filled from the MCP": 1}
    assert keys == {"date": ["courts/2"], "citation": ["courts/2"]}
    line = check.mcp_line({"mcp": out, "mcp disagreements": keys})
    assert "date agrees 1" in line and "date disagrees at courts/2" in line and "NZHC" not in line


def test_the_publish_waits_a_minute_for_its_locks_and_tries_again(monkeypatch):
    # 14 November 2026: the DROP waited 10 minutes on a reader's open transaction and readers queued behind it
    import psycopg
    from registers.courts import load as L
    tries, rests = [], []

    def once(conn, staging):
        tries.append(1)
        if len(tries) < 3:
            raise psycopg.errors.LockNotAvailable("lock timeout")
    monkeypatch.setattr(L, "_publish", once)
    L.publish(None, "s", sleep=rests.append)
    assert len(tries) == 3 and rests == [L.PUBLISH_REST_S] * 2 and L.LOCK_WAIT == "60s"
