#!/usr/bin/env python3
"""One greppable line per lesson — the index LESSONS could not be searched without.

WHY THIS EXISTS. LESSONS is the one document whose entire value is RECALL: a
rule that is not in front of you at the moment you are about to repeat the
mistake has no value at all. The 2026-10-04 split made the file READABLE (eight
sections, each "read when you are about to touch this"), and CLAUDE.md asks a
reader to read the relevant section before touching that area. Measured
2026-10-06, that instruction still cost 99 KB and 122 rules for anything
touching a gate.

And grep — the thing anyone actually reaches for — could not find a rule by its
own claim. **177 of 318 claims span a line break**, because the claim is a
sentence in bold at the head of a wrapped paragraph and grep is line-based. So
`grep -r "preflight below the thing it guards"` found the rule and
`grep -r "A rebuild's DELETE must be as wide as the thing it rebuilds"` did
not, with nothing to tell the searcher which case they were in. A miss reads
exactly like "no rule about this", which is the most expensive wrong answer
this file can give.

WHAT IT GUARANTEES. Every rule appears exactly once, on ONE line, with its
claim intact and the `file:line` to open. That makes three retrievals work that
did not before: grep for a phrase, read the whole index (38 KB, 318 lines) when
you do not know the phrase, and jump straight to the rule's full text with its
scars.

WHAT IT DOES NOT DO. It is an index, not a summary: the claim is the rule's own
first sentence, copied, never rewritten — the scar (the dates, numbers, cards
and paths that make a rule checkable rather than an opinion) stays in the
section file, and `ops/lessons_check.py` is what proves nothing was lost there.

`--check` rides the pre-push doc gate, because a stale index is worse than
none: it is a complete-looking list with a rule missing.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SECTIONS = REPO / "docs/doctrine/lessons"
INDEX = SECTIONS / "INDEX.md"

# A lesson is a top-level bullet, or a numbered failure mode in section 0.
# Continuation lines are indented; a nested bullet belongs to its parent.
START = re.compile(r"^(?:- |\d+\. )")
TITLE = re.compile(r"^(?:- |\d+\. )")

HEADINGS = {
    "0-recurring-failure-modes.md": "The recurring failure modes — read first, always",
    "1-ops-the-estate.md": "1. Ops & the estate — a unit, a timer, a box, a deploy, a backup",
    "2-extraction-rules.md": "2. Extraction & rules — an extractor, a rule, a prompt, a reading",
    "3-measurement-gates.md": "3. Measurement & gates — writing or TRUSTING a gate, arm or measurement",
    "4-capture-sources.md": "4. Capture & sources — a source, a crawler, a fetch, a robots decision",
    "5-agents-llm-lanes.md": "5. Agents & LLM lanes — placing a model, a job, a card, a fleet",
    "6-working-style.md": "6. Working style — planning, writing, closing or handing over a card",
    "7-performance-allocation.md": "7. Performance & allocation — slow, large, hot, or costs too much",
    # SPLIT OUT OF 3 ON 2026-10-09 (C551): section 3 held 182 of 439 rules and
    # 192 KB against T7.38's 160 KB ceiling, because its ROUTING pattern matches
    # building a gate — which every card does — and not a subject.
    "8-reading-documents.md": "8. Reading documents — a profile, a form, a figure, what it is evidence of",
    "9-counting-populations.md": "9. Counting & populations — a sample, a denominator, a counter, a threshold",
}


def claim(block: str) -> str:
    """The rule's own opening claim, on one line, copied and never rewritten.

    The bold lead if there is one — joined across the line breaks that are the
    whole reason this file exists — else the first sentence.
    """
    body = TITLE.sub("", block, count=1)
    one = " ".join(body.split())
    if one.startswith("**"):
        end = one.find("**", 2)
        if end > 0:
            return one[2:end].strip()
    m = re.match(r"(.{20,200}?[.!?])(?:\s|$)", one)
    return (m.group(1) if m else one[:160]).strip()


def scar_date(block: str) -> str:
    """The day the rule was paid for: the latest date in its scars, never a
    date in the future.

    THE ONE FOLD. `ops/lessons_for.py --since` and
    `ops/four_questions.py.filed_on_or_after` both ask "when was this learned",
    and a second implementation is a second answer. It lives here because the
    index is what carries it to every other reader.

    A FUTURE DATE IS NOT A SCAR. The first `--since` run put a rule dated
    2026-11-18 at the top of "filed since 2026-10-05" — a planned muster
    milestone inside the rule's text, not the day anyone learned anything.
    """
    today = _dt.date.today().isoformat()
    return max((d for d in re.findall(r"\b20\d\d-\d\d-\d\d\b", block) if d <= today),
               default="")


def rule_id(claim: str) -> str:
    """A rule's STABLE name: six hex of its claim, not its line number.

    `ops/lessons_for.py` found this by its own retrieval, run against this very
    change: *"never cite a POSITION in a document that is still being written,
    and never key a judgment to a row id something regenerates"*
    (3-measurement-gates.md). A card's LESSONS line cites the rule it read, and
    an anchor of `file:line` goes wrong the moment a rule is appended ABOVE it
    — so the citation would rot, the gate would red honest cards as the
    sections grow, and a gate that cries wolf gets suppressed. Six hex of the
    normalised claim moves only when the CLAIM is rewritten, which is exactly
    when an old citation IS stale.
    """
    return hashlib.sha256(" ".join(claim.lower().split()).encode()).hexdigest()[:6]


def lessons(path: Path) -> list[tuple[int, str]]:
    """(line number, block) for every top-level lesson in a section file."""
    out: list[tuple[int, str]] = []
    cur: list[str] = []
    at = 0
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if START.match(line):
            if cur:
                out.append((at, "\n".join(cur)))
            cur, at = [line], n
        elif cur:
            if line.strip() and not line.startswith((" ", "\t", ">")):
                out.append((at, "\n".join(cur)))
                cur = []
            else:
                cur.append(line)
    if cur:
        out.append((at, "\n".join(cur)))
    return out


#: WHERE A READER IS SENT, and the one place the sizes are true (C551,
#: 2026-10-09). LESSONS.md carried this table by hand and it had ROTTED: it said
#: section 3 was 99 KB when the file was 192 KB, and section 1 37 KB when it was
#: 67 KB. A reader choosing what to open by those numbers was choosing by a
#: figure nobody had updated since the 2026-10-04 split — which is the same
#: defect as "a line that names a gap goes on naming it after the gap closes",
#: in the index of the very corpus that records it. Generated from the files now.
_TABLE_HEAD = "| Section | Read when | Claims | Size |"
READ_WHEN = {
    "0-recurring-failure-modes.md": "first, always — the shapes every other section is an instance of",
    "1-ops-the-estate.md": "touching a unit, a timer, a box, a deploy or a backup",
    "2-extraction-rules.md": "changing an extractor, a rule, a prompt or a reading",
    "3-measurement-gates.md": "writing or trusting a gate, a board arm or an instrument",
    "4-capture-sources.md": "adding a source, a crawler, a fetch or a robots decision",
    "5-agents-llm-lanes.md": "placing a model, a job, a card or a fleet decision",
    "6-working-style.md": "planning work, writing a card, closing one, or handing over",
    "7-performance-allocation.md": "something is slow, large, hot, or costs more than it should",
    "8-reading-documents.md": "reading a document — a profile, a form, a figure, what it proves",
    "9-counting-populations.md": "counting — a sample, a denominator, a counter, a threshold",
}
LESSONS_MD = REPO / "docs/doctrine/LESSONS.md"


def render_table() -> str:
    files = sorted(p for p in SECTIONS.glob("*.md") if p.name != "INDEX.md")
    rows = [_TABLE_HEAD, "| --- | --- | --- | --- |"]
    tot_b = tot_c = 0
    for p in files:
        n, b = len(lessons(p)), p.stat().st_size
        tot_b += b
        tot_c += n
        title = HEADINGS.get(p.name, p.name).split(" — ")[0]
        rows.append(f"| [{title}](lessons/{p.name}) | {READ_WHEN.get(p.name, '')} "
                    f"| {n} | {b // 1024} KB |")
    big = max(files, key=lambda q: q.stat().st_size)
    rows += ["", f"Total {tot_b:,} B and {tot_c} claims across {len(files)} files; largest "
                 f"{big.name} at {big.stat().st_size // 1024} KB against T7.38's 160 KB "
                 f"one-read ceiling. GENERATED by `ops/lessons_index.py --write`."]
    return "\n".join(rows) + "\n"


def patch_lessons_md() -> bool:
    """Replace the sections table in LESSONS.md. Returns True if it changed."""
    if not LESSONS_MD.exists():
        return False
    txt = LESSONS_MD.read_text()
    start = txt.find(_TABLE_HEAD)
    if start < 0:
        start = txt.find("| Section | Read when |")
    if start < 0:
        return False
    # The block ends at the blank line after the table's trailing summary — or
    # at END OF FILE, which is where it actually sits and which the first
    # version of this returned False on rather than noticing (a reader of that
    # False would have concluded the table was already current).
    tot = txt.find("Total ", start)
    if tot < 0:
        return False
    end = txt.find("\n\n", tot)
    tail = "" if end < 0 else txt[end + 1:]
    want = txt[:start] + render_table() + tail
    if want == txt:
        return False
    LESSONS_MD.write_text(want)
    return True


def render() -> str:
    files = sorted(p for p in SECTIONS.glob("*.md") if p.name != "INDEX.md")
    total = sum(len(lessons(p)) for p in files)
    out = [
        "# LESSONS — the index of claims",
        "",
        "> GENERATED by `ops/lessons_index.py`; `--check` rides the pre-push doc gate.",
        "> Do not edit by hand — append the rule to its SECTION, then regenerate.",
        ">",
        "> One line per rule, carrying the rule's own opening claim and where to",
        "> open it. **This is the grep target.** The sections wrap their claims",
        "> across lines, so a line-based search of them misses most rules; a",
        f"> search of this file cannot. {total} rules.",
        ">",
        "> Each rule carries `file:line` (where to OPEN it), `#id` (how to CITE it —",
        "> six hex of the claim, stable when the file is edited above it) and the",
        "> date of its latest scar (what `--since` and the close gate read).",
        "",
        "Reading it whole is {:.0f} KB and is the right move when you do not yet".format(
            0),  # replaced below
        "",
    ]
    del out[-2:]
    out += ["Reading it whole is the right move when you do not yet know the phrase",
            "to search for — which is the usual case at the start of a card.", ""]
    for p in files:
        out.append(f"## [{HEADINGS.get(p.name, p.name)}]({p.name})")
        out.append("")
        for n, block in lessons(p):
            c = claim(block)
            # the scar date is ON THE INDEX LINE, because the gate that asks
            # "was a lesson filed at this close" reads the index — and a date
            # that lives only in the body is a date that check cannot see.
            # That miss was the first thing this ritual caught in itself.
            d = scar_date(block)
            out.append(f"- {c} — `{p.name}:{n}` #{rule_id(c)}" + (f" ({d})" if d else ""))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the index is not what regeneration would write")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    want = render()
    have = INDEX.read_text() if INDEX.exists() else ""
    if a.check:
        # THE TABLE IS CHECKED TOO, or it rots exactly as it did before C551 —
        # a generated artifact nothing verifies is a hand-maintained one with
        # extra steps. `patch_lessons_md` is a no-op when the table is current,
        # so "would it change?" is asked without writing.
        table_stale = False
        if LESSONS_MD.exists():
            before = LESSONS_MD.read_text()
            table_stale = patch_lessons_md()
            if table_stale:
                LESSONS_MD.write_text(before)      # --check never writes
        if want == have and not table_stale:
            print(f"ok    lessons index current ({want.count(chr(10) + '- ')} rules) "
                  f"and LESSONS.md's sections table current")
            return 0
        if table_stale and want == have:
            print("fail  LESSONS.md's sections table is stale — run "
                  "ops/lessons_index.py --write")
            return 1
        import difflib
        d = [l for l in difflib.unified_diff(have.splitlines(), want.splitlines(),
                                             "INDEX.md", "regenerated", lineterm="", n=0)][:40]
        print("fail  the lessons index is stale — run ops/lessons_index.py --write")
        print("\n".join(d))
        return 1
    if a.write:
        INDEX.write_text(want)
        print(f"wrote {INDEX.relative_to(REPO)} — {want.count(chr(10) + '- ')} rules, "
              f"{len(want) / 1024:.1f} KB")
        if patch_lessons_md():
            print(f"wrote {LESSONS_MD.relative_to(REPO)} — sections table regenerated")
        return 0
    sys.stdout.write(want)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
