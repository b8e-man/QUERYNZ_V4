#!/usr/bin/env python3
"""The lessons for the thing you are about to touch — BEFORE you touch it.

    python -B ops/lessons_for.py                        # for the working tree's changes
    python -B ops/lessons_for.py --card C511            # for a card, by its row
    python -B ops/lessons_for.py --paths ops/x.py --words "preflight gate"
    python -B ops/lessons_for.py --card C511 --anchors  # just the anchors, to paste

ARTHUR, 2026-10-06: *"we want to get the appropriate lessons before we build or
change anything so build this in."*

WHY A TOOL AND NOT A DISCIPLINE. The estate already had the rules (318 of them
on 2026-10-06, when this was built; `rule_count()` reads today's number, because a
footer that tells a reader the corpus is smaller than it is argues against itself)
and the instruction to read them — MO.md §150 says *"read the lessons for this
area FIRST"*, and CLAUDE.md asks for the relevant section before touching that
area. Both were true and neither was happening, because the cheapest honest
reading of "the relevant section" was 99 KB and 122 rules, and the fast path —
grep — silently missed 177 of 318 claims (they wrap across lines; see
`ops/lessons_index.py`). A discipline whose correct execution costs that much
is not a discipline, it is an intention.

WHAT IT IS. Lexical retrieval over the rules, keyed on what you are about to
change: the paths in your diff or on the command line, a card's own row, and
any words you add. It prints the recurring failure modes WHOLE every time —
twelve lines, and they are the shapes every other rule is an instance of — then
the ranked rules with the `file:line` to open each one.

WHAT IT IS NOT, MEASURED. `--selftest` runs eight real pairs — a card closed
here, and the claim of the rule that would have warned it — and scores
**5 of 8, and 2 of the 5 a rule ALREADY covered.** That is the ceiling of
lexical retrieval and it is printed, not buried: the words of a card and the
words of its lesson are frequently disjoint. C037's card said *"embed-backfill
runs at 2/s — tune the rate"*; its lesson says *"a lane that cannot call the
model must not report an empty document"*. Not one shared word, because the
card describes a performance question and the defect was a reporting one — the
connection became visible from the CODE, not from the card. Adding the files'
own vocabulary to the query was tried and measured: it improves some ranks,
worsens others, and fixes none of the three misses.

So the ranked list is the SPECIFICITY layer and it is not the recall layer.
Recall is carried by the two things printed every run regardless of score: the
twelve recurring failure modes (mode 11 alone accounts for eight of the nine
defects found on 2026-10-05), and the full claim list of the sections your
paths point at. A thin result means "search again in your own words", and
NEVER "there is no rule about this".

HONEST ABOUT THE GATE. `ops/four_questions.py` can check that a card NAMED its
lessons; nothing can check that a person read them. Naming them by anchor, and
verifying the anchors exist and are among what retrieval returns for that
card's own subject, is the closest achievable thing — and that gap is stated
rather than papered over, because a check adjacent to the question it claims to
answer is this estate's characteristic failure (mode 11).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import math
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lessons_index as L  # the ONE parser for the rules; never a second fold

REPO = pathlib.Path(__file__).resolve().parents[1]
TODAY = _dt.date.today().isoformat()
LIVE = REPO / "data-layer/docs/MUSTER_2_CARDS.md"
CLOSED = REPO / "data-layer/docs/MUSTER_2_CARDS_CLOSED.md"

#: Words carrying no retrieval signal in THIS corpus. Deliberately short: a
#: long stop-list is a way of deciding, silently, which rules can be found.
STOP = set("""a an and are as at be been before but by can cannot do does for from
has have how if in into is it its must never no not of on once one only or our out
so than that the their them then there these they this to too two up was were what
when where which who why will with without you your we us i me my about after all
also any because both each either else every few more most much neither new now
other over per same some such take takes very via while whose would should could""".split())

#: A changed path suggests a section even when its words do not. The patterns
#: are the ones the sections' own headings describe, and the boost is small on
#: purpose — it orders ties, it does not outrank a direct hit.
AFFINITY: tuple[tuple[str, str], ...] = (
    (r"ops/systemd/|\.service$|\.timer$|ops/production/|deploy|backup|offsite|systemctl|journal",
     "1-ops-the-estate.md"),
    (r"extractor/|prompts?/|registers/|claim_graph/|normalis|candidate_register|healer/|reread",
     "2-extraction-rules.md"),
    (r"^tests/|test_|_check\.py$|gate|invariants|board|coverage_scan|audit",
     "3-measurement-gates.md"),
    (r"ingestion/|fetchgate|robots|scraper|crawl|capture|hansard|pageread",
     "4-capture-sources.md"),
    (r"llm|model|fleet|agent|slots|embed|vision|ocr|modelgate",
     "5-agents-llm-lanes.md"),
    (r"^docs/|\.md$|MUSTER|daylog|ledger|card|SPEC",
     "6-working-style.md"),
    (r"\.sql$|postgres|wal|index|vacuum|explain|dsn|connection|memory|psi|disk",
     "7-performance-allocation.md"),
    # SPLIT OUT OF 3 ON 2026-10-09 (C551). Section 3's pattern above matches
    # building a gate, which EVERY card here does, so it accumulated 182 of the
    # corpus's 439 rules. These two name SUBJECTS instead. Nothing was removed
    # from section 3's pattern: a card about reading a form matches both, and
    # `section_claims` returns every match rather than the first.
    (r"profile|pageread|ocr|scan|form|figure|declaration|disclosure|document|_read|reader",
     "8-reading-documents.md"),
    (r"sample|census|denominator|population|counter|threshold|floor|count|rate|percent|median",
     "9-counting-populations.md"),
)

MODES = "0-recurring-failure-modes.md"
_WORD = re.compile(r"[a-z0-9_]{3,}")
_CARD = re.compile(r"\bC\d{3,4}\b")


def rule_count() -> int:
    """How many rules the corpus holds RIGHT NOW, read from the generated
    index. It was 318 when this tool shipped on 2026-10-06 and the number was
    written into three strings; nineteen rules were filed on 2026-10-05 alone,
    so by 2026-10-08 the tool was telling every reader the corpus was 97 rules
    smaller than it is — while its own purpose is to say "that thin result is
    not 'there is no rule about this'". A count that argues against the
    sentence around it is worse than no count."""
    try:
        idx = pathlib.Path(__file__).resolve().parents[1] / "docs" / "doctrine" \
            / "lessons" / "INDEX.md"
        return sum(1 for l in idx.read_text().splitlines() if l.startswith("- "))
    except Exception:                                   # noqa: BLE001
        return 0


def words(text: str) -> list[str]:
    """Lower-case terms, card ids REMOVED.

    Card ids are stripped from both sides. A rule written from C008 names C008,
    so leaving them in would let a card retrieve its own lesson by its number —
    which measures nothing, and would make `--selftest` a self-fulfilling
    report of the one thing it exists to question.
    """
    return [w for w in _WORD.findall(_CARD.sub(" ", text).lower()) if w not in STOP]


def path_terms(p: str) -> list[str]:
    """A path as search terms: its parts, and its stem split on _ and -."""
    out: list[str] = []
    for part in re.split(r"[/]", p):
        out += [t for t in re.split(r"[-_.]", part.lower()) if len(t) >= 3 and t not in STOP]
    return out


class Corpus:
    """Every rule, once, with the vocabulary to rank it."""

    def __init__(self) -> None:
        self.rules: list[dict] = []
        for f in sorted(L.SECTIONS.glob("*.md")):
            if f.name in (L.INDEX.name, MODES):
                continue
            for n, block in L.lessons(f):
                claim = L.claim(block)
                self.rules.append({
                    "file": f.name, "line": n, "claim": claim,
                    "anchor": f"{f.name}:{n}",
                    "claim_terms": set(words(claim)),
                    "terms": set(words(block)),
                    "paths": {m.lower() for m in re.findall(
                        r"(?<![\w/])((?:[\w.-]+/)+[\w.-]+\.\w{1,5})\b", block)},
                    #: the latest date in the rule's scars — what `--since`
                    #: filters on for the EXECUTION check. A rule's scars carry
                    #: the day it was paid for, which is the only date the file
                    #: has; git would give the commit, which for the 2026-10-04
                    #: split is the day every rule MOVED, not the day it was
                    #: learned.
                    #:
                    #: ONE FOLD, in lessons_index — the index carries it to
                    #: the close gate too, and two implementations of "when was
                    #: this learned" would be two answers.
                    "last": L.scar_date(block),
                })
        n = len(self.rules)
        self.idf = {}
        df: dict[str, int] = {}
        for r in self.rules:
            for t in r["terms"]:
                df[t] = df.get(t, 0) + 1
        for t, c in df.items():
            self.idf[t] = math.log(1 + n / c)

    def modes(self) -> list[tuple[int, str]]:
        f = L.SECTIONS / MODES
        return [(n, L.claim(b)) for n, b in L.lessons(f)]

    def since(self, when: str) -> list[dict]:
        """Rules whose scars are dated on or after `when`, newest first.

        RULING 359's second half (Arthur, 2026-10-06): *"when we address a card
        we want to check again incase there is something new and good."* The
        corpus moves — nineteen rules were filed on 2026-10-05 alone — so a
        card planned one week and built the next was planned against a corpus
        that no longer exists. Re-reading the same ranked list would be
        theatre; this is the part that can have changed.
        """
        return sorted((r for r in self.rules if r["last"] >= when),
                      key=lambda r: r["last"], reverse=True)

    def section_claims(self, signals: list[str]) -> list[tuple[str, list[str]]]:
        """Every claim of the sections your paths point at.

        The ranked list cannot bridge a query whose words the rule does not
        use — measured at three misses in eight. This is the layer that does
        not depend on sharing a word: a bounded list (the biggest section is
        122 claims) that you SCAN. It is why a zero-overlap query still gets
        something to read instead of a confident empty answer.
        """
        secs = [s for pat, s in AFFINITY if any(re.search(pat, g, re.I) for g in signals)]
        out = []
        for s in secs:
            f = L.SECTIONS / s
            if f.exists():
                out.append((s, [L.claim(b) for _, b in L.lessons(f)]))
        return out

    def rank(self, terms: list[str], paths: list[str], top: int,
             signals: list[str] | None = None) -> list[dict]:
        q = [t for t in terms if t in self.idf]
        # A card that names no file still says what it is about. Affinity reads
        # the subject TEXT as well as the paths, because `--card C500` has only
        # prose and was getting no section at all.
        sig = list(signals or []) + list(paths)
        sections = {s for pat, s in AFFINITY for g in sig if re.search(pat, g, re.I)}
        scored = []
        for r in self.rules:
            s = 0.0
            for t in set(q):
                if t in r["claim_terms"]:
                    s += 3.0 * self.idf[t]
                elif t in r["terms"]:
                    s += 1.0 * self.idf[t]
            # a rule that NAMES a file you are changing is about your change
            for p in paths:
                pl = p.lower()
                if pl in r["paths"]:
                    s += 25.0
                elif any(pl.endswith("/" + c.split("/")[-1]) or c.endswith("/" + pl.split("/")[-1])
                         for c in r["paths"]):
                    s += 8.0
            if s and r["file"] in sections:
                s *= 1.25
            if s:
                scored.append((s, r))
        scored.sort(key=lambda x: (-x[0], x[1]["anchor"]))
        return [dict(r, score=round(s, 1)) for s, r in scored[:top]]


def changed_paths() -> list[str]:
    """What the working tree is changing, staged or not, vs HEAD."""
    out = set()
    for args in (["diff", "--name-only", "HEAD"], ["diff", "--name-only", "--cached"],
                 ["ls-files", "--others", "--exclude-standard"]):
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=REPO)
        out |= {l.strip() for l in r.stdout.splitlines() if l.strip()}
    return sorted(p for p in out if not p.startswith("docs/doctrine/lessons/"))


def card_subject(cid: str) -> tuple[str, list[str]]:
    """A card's own words, and any paths its row names."""
    for path in (LIVE, CLOSED):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if line.startswith(f"| {cid} |"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                text = " ".join(cells[1:4])
                paths = re.findall(r"(?<![\w/])((?:[\w.-]+/)+[\w.-]+\.\w{1,5})\b", line)
                return text, paths
    return "", []


def card_raised(cid: str) -> str:
    """The date a card was raised, from its row — the natural `--since`."""
    for path in (LIVE, CLOSED):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if line.startswith(f"| {cid} |"):
                m = re.search(r"\braised (\d{4}-\d{2}-\d{2})", line)
                if m:
                    return m.group(1)
    return ""


def report(terms: list[str], paths: list[str], top: int, subject: str,
           anchors_only: bool = False, text: str = "", since: str = "") -> str:
    c = Corpus()
    signals = [text] + paths
    hits = c.rank(terms, paths, top, signals)
    if anchors_only:
        return " ".join(f"{h['anchor']} #{L.rule_id(h['claim'])}" for h in hits)
    out = [f"LESSONS BEFORE YOU BUILD — {subject}", ""]
    if since:
        # RANKED, NOT CHRONOLOGICAL. The first version listed every rule filed
        # since the date, newest first — and on a card raised 2026-09-19 that is
        # 210 of 321 rules, which is no more useful than reading the index and
        # reads as though the tool had nothing to say. The second check is
        # "what is NEW *and* about my card", so the fresh set is scored by the
        # same relevance as everything else and the remainder is COUNTED rather
        # than dumped. (Found running it on C216, 2026-10-06.)
        fresh = {r["anchor"] for r in c.since(since)}
        ranked = [h for h in c.rank(terms, paths, 400, signals) if h["anchor"] in fresh]
        out.append(f"FILED SINCE {since} AND RELEVANT — {len(ranked)} of {len(fresh)} new "
                   f"rule(s) score against this card. This is the half that can have changed "
                   f"since it was planned.")
        for r in ranked[:10]:
            out.append(f"   · [{r['last']}] {r['claim']}")
            out.append(f"       `{r['anchor']}` #{L.rule_id(r['claim'])}  score {r['score']}")
        if not fresh:
            out.append("   (nothing — the corpus has not moved since the card was planned)")
        elif not ranked:
            out.append(f"   (none of the {len(fresh)} new rules scores against this card — "
                       f"they are listed by date in lessons/INDEX.md)")
        out.append("")
    out.append("THE RECURRING FAILURE MODES — the shapes the rest are instances of")
    for n, claim in c.modes():
        out.append(f"   {claim}   [{MODES}:{n}]")
    out.append("")
    if not hits:
        out += ["No rule matched those words. That is NOT 'there is no rule about this' —",
                "search again in your own words, or read the section whole:",
                f"  docs/doctrine/lessons/ (INDEX.md is one line per rule, "
                f"{rule_count()} of them)."]
        return "\n".join(out)
    secs: dict[str, int] = {}
    for h in hits:
        secs[h["file"]] = secs.get(h["file"], 0) + 1
    out.append(f"THE {len(hits)} CLOSEST RULES — open each at its anchor for the scars")
    for i, h in enumerate(hits, 1):
        out.append(f"{i:3}. {h['claim']}")
        out.append(f"      [{h['anchor']}]  score {h['score']}")
    out.append("")
    best = max(secs, key=lambda k: secs[k])
    out.append(f"READ WHOLE if you are doing anything substantial here: {best} "
               f"({secs[best]} of the top {len(hits)})")
    out.append("")
    # the layer that does not need a shared word — see Corpus.section_claims
    for sec, claims in c.section_claims(signals)[:2]:
        out.append(f"EVERY CLAIM IN {sec} ({len(claims)}) — scan it; the ranked list "
                   f"above cannot find a rule whose words you did not type")
        for cl in claims:
            out.append(f"   · {cl}")
        out.append("")
    out.append("If none of the above is it, that is not 'no rule about this': "
               f"docs/doctrine/lessons/INDEX.md is all {rule_count()}, one line each.")
    out.append("CITE (for the card's LESSONS line — the #id is the durable half, "
               "the path:line is where to open it):")
    for h in hits[:6]:
        out.append(f"   `{h['anchor']}` #{L.rule_id(h['claim'])}")
    return "\n".join(out)


#: (what you would have had at card-open) -> (a phrase from the claim of the
#: rule that would have warned you). REAL pairs, all eight cards closed in this
#: estate on 2026-10-05.
#:
#: FIVE ARE PRE-EXISTING RULES — the rule was in LESSONS before the card was
#: worked, and nobody looked. Those are the ones that measure anything: if
#: retrieval had existed, the mistake was avoidable. THREE point at rules
#: written from the card itself, which measures the opposite and still useful
#: thing — that today's rule is retrievable by someone arriving at the same
#: problem tomorrow with none of today's words.
#:
#: Card ids are stripped from both query and corpus by `words()`, so no pair
#: can be satisfied by its own number. The expectation is a phrase from the
#: rule's CLAIM, not an anchor, because anchors move whenever a section is
#: edited above them and a labelled set that rots is worse than none.
SELFTEST: tuple[tuple[str, str, list[str], str, bool], ...] = (
    ("C037", "the embed backfill runs at two a second, five hours a pass, tune the rate",
     ["ops/embed_articles.py"], "must not report an empty document", True),
    ("C501", "the hansard lane reports an empty house and exits clean",
     ["ingestion/hansard/scraper.py", "ingestion/hansard/forward.py"],
     "must not report an empty document", True),
    ("C457", "fold the alias keys, a set-based migration over seventy-eight million rows",
     ["ops/alias_refold.py", "data-layer/claim_graph/claim_graph/normalise.py"],
     "bounded, audited and reversible", True),
    ("C059", "the nightly offsite push stopped and nothing restarted it",
     ["ops/systemd/offsite-push.service"], "restart policy and a watcher", True),
    ("C061", "the health endpoint should say which database answered",
     ["data-layer/estate-dsn/estate_dsn.py"], "postgres's own traps", True),
    ("C008", "how wide may the extraction fleet be, how many shards",
     ["ops/extract_fleet.py"], "spend the serving tier", False),
    ("C500", "the coverage scan calls a quiet day sparse",
     ["ops/coverage_scan.py"], "cannot see a weekday", False),
    ("C510", "the release checks the public url after the flip",
     ["ops/pi_release.py"], "read a published thing back more than once", False),
)


def selftest(top: int = 20) -> tuple[int, int, str]:
    """Measured recall, reporting the misses BY NAME and separating the pairs a
    pre-existing rule should have caught from the pairs that only prove today's
    rules are findable. A retrieval tool that reports one blended hit rate is
    the instrument lying about itself."""
    c = Corpus()
    lines, hit, pre_hit, pre_n = [], 0, 0, 0
    for cid, text, paths, expect, pre in SELFTEST:
        terms = words(text) + [t for p in paths for t in path_terms(p)]
        got = c.rank(terms, paths, top, [text] + paths)
        where = next((i for i, h in enumerate(got, 1)
                      if expect in h["claim"].lower()), None)
        hit += where is not None
        pre_n += pre
        pre_hit += pre and where is not None
        lines.append(f"  {cid:5} {'pre' if pre else 'new'} "
                     f"{('#' + str(where)) if where else 'MISS':>5}  {expect!r}")
    lines.append(f"  recall@{top}: {hit}/{len(SELFTEST)} = {hit / len(SELFTEST):.0%}"
                 f"   — of the {pre_n} a rule ALREADY covered: {pre_hit}/{pre_n}")
    return hit, pre_hit, "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--card", help="a card id; its row supplies the subject")
    ap.add_argument("--paths", nargs="*", default=[], help="files you are about to change")
    ap.add_argument("--words", default="", help="what you are about to do, in your words")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--anchors", action="store_true", help="just the anchors, to paste into a card")
    ap.add_argument("--since", nargs="?", const="card", metavar="YYYY-MM-DD",
                    help="the EXECUTION check: what has been filed since. Bare, with "
                         "--card, uses the date the card was raised")
    ap.add_argument("--selftest", action="store_true", help="measured recall on the labelled set")
    a = ap.parse_args(argv)

    if a.selftest:
        hit, pre_hit, text = selftest()
        print("RETRIEVAL SELFTEST — real (card, rule-that-would-have-warned) pairs")
        print(text)
        return 0 if hit >= len(SELFTEST) * 0.6 else 1

    paths = list(a.paths)
    text = a.words
    since = a.since or ""
    subject_bits = []
    if a.card:
        ct, cp = card_subject(a.card)
        if not ct:
            print(f"no row for {a.card} in the live or closed register", file=sys.stderr)
            return 2
        text = (text + " " + ct).strip()
        paths += cp
        subject_bits.append(a.card)
        if since == "card":
            since = card_raised(a.card) or ""
            if not since:
                print(f"{a.card}'s row carries no 'raised <date>' — pass --since a date",
                      file=sys.stderr)
                return 2
    if since == "card":
        print("--since with no date needs --card", file=sys.stderr)
        return 2
    if not paths and not a.words and not a.card:
        paths = changed_paths()
        subject_bits.append(f"{len(paths)} changed file(s) in the working tree")
    if a.paths or (a.card and paths):
        subject_bits.append(", ".join(sorted(set(paths))[:6]) or "no paths")
    if a.words:
        subject_bits.append(repr(a.words))
    if not paths and not text:
        print("nothing to go on: pass --paths, --words or --card, or change something first")
        return 2
    terms = words(text) + [t for p in paths for t in path_terms(p)]
    print(report(terms, paths, a.top, " · ".join(subject_bits), a.anchors, text, since))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
