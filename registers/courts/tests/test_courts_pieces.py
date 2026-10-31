"""The profile check (ruling 130): every courts profile the text reader
reads carries a reading rule within the text-reader context; a document
over its budget is split by the rule, the caption first and whole, no
paragraph in two pieces, every piece within the budget; a document the
rule cannot split is named. Invented pages; no model, no database."""
import re

import pytest

from support import profiles
from registers.courts import caption
from registers.courts import pieces as PC
from registers.courts import read as R
from registers.courts.model_read import MAX_TOKENS, PROMPT

CONTEXT_TOKENS, WORST_CHARS_PER_TOKEN = 16384, 3.0      # the text-reader profile's context; the ledger's worst ratio was 3.3


def _judgment(paragraphs: int, per_page: int = 6, words: int = 60) -> dict:
    pages = {1: "IN THE SUPREME COURT OF NEW ZEALAND\n" + " " * 60 + "[2099] NZSC 7\n" + " " * 15 + "BETWEEN  EXAMPLE HOLDINGS LIMITED\n"
             + " " * 44 + "Appellant\nJudgment:  2 June 2099\n\n     JUDGMENT OF THE COURT\n"}
    n, page = 1, 2
    while n <= paragraphs:
        body = ""
        for _ in range(per_page):
            if n > paragraphs:
                break
            body += f"[{n}]  " + f"Paragraph {n} says things. " * words + "\n\n"
            n += 1
        pages[page] = body
        page += 1
    return pages


def test_every_profile_the_text_reader_reads_carries_a_rule_within_the_context():
    for slug in sorted(R.TEXT_READ_SLUGS):
        rule = PC.rule_of(slug)
        assert rule["split"] in PC.SPLITS, slug
        prompt_tokens = len(PROMPT) / WORST_CHARS_PER_TOKEN + 200
        assert rule["budget_chars"] / WORST_CHARS_PER_TOKEN + MAX_TOKENS + prompt_tokens <= CONTEXT_TOKENS, \
            f"{slug}: a piece of {rule['budget_chars']} characters plus the answer and the prompt does not fit {CONTEXT_TOKENS} tokens at {WORST_CHARS_PER_TOKEN} chars/token"
        p = R.profile_of(slug)
        assert p["reading"]["context_tokens"] == CONTEXT_TOKENS and p["reading"]["answer_tokens"] == MAX_TOKENS, slug
    expected = {"whole": {R.CASE_PAGE, R.RELEASE, R.SYNOPSIS}, "pages": {R.TRANSCRIPT}, "numbered": {R.SUBMISSION}}
    for split, slugs in expected.items():
        for slug in slugs:
            assert PC.rule_of(slug)["split"] == split, slug
    for slug in R.JUDGMENT_SLUGS:
        assert PC.rule_of(slug)["split"] == "paragraphs", slug
    with pytest.raises(LookupError):
        PC.rule_of("courts-scanned-document")      # read by the page reader, then recognised again: no text rule of its own
    with pytest.raises(LookupError):
        PC.rule_of("courts-nzsc-judgment", profile_of=lambda s: {"reading": {"budget_chars": 34000, "split": "halves"}})


def test_the_proposed_lines_are_the_ledger_s_next_versions_and_say_who_and_when():
    cur = profiles.current(R.PROPOSED)
    ledger = profiles.current()
    for slug, p in cur.items():
        assert p["version"] == (int(ledger[slug]["version"]) if slug in ledger else 0) + 1, slug
        assert p["by"] and p["at"] and p["title"] and p["recognise"] and p["signals"], slug
        assert R.profile_of(slug) is not None and R.profile_version(slug) == p["version"]
    assert {"courts-era-determination", "courts-hrrt-decision", "courts-tribunal-decision", "courts-nzdc-judgment"} <= set(cur)
    assert "courts-scanned-document" not in cur, "the scanned profile keys the stored page readings: its version stands"


def test_a_short_document_is_one_piece_whatever_the_rule():
    texts = _judgment(4)
    for split in PC.SPLITS:
        parts, why = PC.plan(texts, {"budget_chars": 34000, "split": split})
        assert len(parts) == 1 and why is None and parts[0].startswith("[page 1]\nIN THE SUPREME COURT")


def test_a_judgment_splits_at_its_numbered_paragraphs_the_caption_first_and_whole():
    texts = _judgment(200)
    whole = PC.body_of(texts)
    rule = {"budget_chars": 34000, "split": "paragraphs"}
    parts, why = PC.plan(texts, rule)
    assert why is None and len(parts) >= 5
    assert all(len(p) <= rule["budget_chars"] for p in parts), [len(p) for p in parts]
    assert parts[0].startswith("[page 1]\nIN THE SUPREME COURT") and "[1]  Paragraph 1" in parts[0]
    for i, p in enumerate(parts[1:], 2):
        assert p.startswith(f"[part {i} of {len(parts)} of the document"), "a later piece says which it is"
        assert "IN THE SUPREME COURT OF NEW ZEALAND" in p.splitlines()[1], "and opens with the document's first lines"
        body = p.split("[…]\n\n", 1)[1]
        assert re.match(r"(\[page \d+\]\n)?\[\d+\]  Paragraph", body), "a piece opens at a paragraph (or the page it starts on)"
    # every paragraph is in exactly one piece, whole
    for n in range(1, 201):
        marker = f"[{n}]  Paragraph {n} says"
        holders = [p for p in parts if marker in p]
        assert len(holders) == 1, n
        assert (f"Paragraph {n} says things. " * 60).strip() in holders[0], f"paragraph {n} is cut"
    assert sum(len(p.split("[…]\n\n", 1)[-1]) for p in parts) >= len(whole) - 20 * len(parts), "nothing is dropped"


def test_a_run_longer_than_the_budget_is_cut_at_its_pages_and_a_page_over_the_budget_cannot_be_split():
    texts = _judgment(2)
    texts[3] = "An annex with no numbered paragraphs. " * 600      # 23,000 characters after the last paragraph …
    texts[4] = "More of the annex. " * 1200                          # … and 23,000 more on the next page: one run of 46,000
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "paragraphs"})
    assert why is None and len(parts) >= 2, "the run after [2] is cut at its page break"
    texts = {1: "IN THE SUPREME COURT OF NEW ZEALAND\n[1]  First.\n[2]  Second.\n", 2: "x" * 40000}
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "paragraphs"})
    assert parts is None and "a page of 40,0" in why and "exceeds the budget" in why


def test_a_long_document_with_no_numbered_paragraphs_cannot_be_split_and_is_named():
    texts = {p: f"Page {p}. " * 2000 for p in range(1, 4)}       # 54,000 characters, no [n]
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "paragraphs"})
    assert parts is None and "fewer than two numbered paragraphs" in why and "paragraphs" in why
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "whole"})
    assert parts is None and "the rule for this profile is whole" in why
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "pages"})
    assert why is None and len(parts) == 2 and parts[1].split("[…]\n\n", 1)[1].startswith("[page 3]"), "a transcript is read by pages, packed"
    assert PC.count(texts, {"budget_chars": 34000, "split": "pages"}) == 2 and PC.count(texts, {"budget_chars": 34000, "split": "whole"}) is None


def test_submissions_split_at_paragraphs_numbered_with_a_dot():
    texts = {1: "IN THE SUPREME COURT OF NEW ZEALAND\nSUBMISSIONS OF COUNSEL FOR THE APPELLANT\n"}
    for p in range(2, 8):
        texts[p] = "".join(f"{n}.  " + "Submission text. " * 150 + "\n\n" for n in range((p - 2) * 5 + 1, (p - 2) * 5 + 6))
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "numbered"})
    assert why is None and len(parts) >= 2
    assert all(len(p) <= 34000 for p in parts)
    for n in range(1, 31):
        assert sum(f"\n{n}.  Submission text." in p or p.split("[…]\n\n", 1)[-1].startswith(f"[page") and f"{n}.  Submission" in p for p in parts) >= 1, n


def test_a_transcript_page_over_the_budget_is_cut_at_its_speaker_turns():
    turns = "".join(f"{'ABLE CJ' if i % 2 else 'MR ROWE KC'}:\n" + "Spoken words here. " * 100 + "\n" for i in range(40))
    texts = {1: "IN THE SUPREME COURT OF NEW ZEALAND\n[2099] NZSC Trans 9\n", 2: turns}
    assert len(turns) > 34000
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "pages"})
    assert why is None and len(parts) >= 3 and all(len(p) <= 34000 for p in parts)
    for p in parts[1:]:
        body = p.split("[…]\n\n", 1)[1]
        assert re.match(r"(\[page 2\]\n)?(ABLE CJ|MR ROWE KC):", body), "a cut falls at a speaker's turn"


def test_the_paragraph_marker_is_the_caption_grammar_s_own():
    assert PC._para_marker("[12]  The twelfth.") == 12 and PC._para_marker("   [2024] NZSC 161 at [45]") is None
    assert PC._para_marker("[13]  The thirteenth.") == int(caption.PARA.match("[13]  The thirteenth.").group(2)) == 13
    assert PC._para_marker("      [14]  Quoted from another judgment, indented deep") == 14 and PC._para_marker(" " * 14 + "[15]  deeper") is None
    assert PC._numbered_marker("3.  Third submission.") == 3 and PC._numbered_marker("[3]  Third.") == 3 and PC._numbered_marker("3.5 metres") == 3   # the sequence check guards a measurement at the margin
    assert PC._numbered_marker("3.1  A sub-paragraph.") == 3 and PC._numbered_marker("12.4.  Deeper.") == 12 and PC._numbered_marker("3.  ") is None


def test_a_determination_numbered_with_dots_splits_at_those_numbers():
    texts = {1: "IN THE EMPLOYMENT RELATIONS AUTHORITY\n[2099] NZERA 1\nDETERMINATION OF THE AUTHORITY\n"}
    for p in range(2, 9):
        texts[p] = "".join(f"{n}.  " + "Determination text. " * 150 + "\n\n" for n in range((p - 2) * 4 + 1, (p - 2) * 4 + 5))
    parts, why = PC.plan(texts, {"budget_chars": 34000, "split": "paragraphs"})
    assert why is None and len(parts) >= 2 and all(len(p) <= 34000 for p in parts)
    for p in parts[1:]:
        assert re.match(r"(\[page \d+\]\n)?\d+\.  Determination", p.split("[…]\n\n", 1)[1]), "a later piece opens at a numbered paragraph"
