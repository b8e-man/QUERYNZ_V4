# LESSONS — what this project has paid to learn

> KIND: **living memory** (a kind of its own — not doctrine, not a record).
> Doctrine changes only by ruling; a lesson is appended the DAY it is learned,
> by whoever learned it.
>
> **Why this file exists.** On 2026-08-20 a fix to the sweep didn't reach the
> already-running process and the job crashed twice on the line we'd just
> fixed. Writing that up, we found the same lesson already recorded — in
> 2026-07, as SCRAPERS.md lesson 17, in a heritage doc nobody opens. The lesson
> had been learned, written down, and lost. **A lesson filed in a dated record
> is functionally forgotten**: its whole value is being recalled at the moment
> you are about to repeat it.
>
> **Rules of this file**
> 1. Append the day it's learned — not at the next audit.
> 2. One self-contained sentence per RULE. Someone reading only that line must
>    get it, with no other context.
> 3. Name the incidents that bought it, with numbers. A rule without its scars
>    reads as an opinion — so every rule carries a **Paid for by** list, and a
>    new incident is appended to the rule it belongs to, not filed as a new
>    rule.
> 4. GRADUATION: when a rule hardens into a standing rule it moves to its
>    doctrine/SPEC home and stays here as a one-line pointer.
> 5. Sections are "when it bites", not "where it came from" — you find a rule
>    by the situation you're in.
> 6. A rule the architecture has made structurally impossible is DELETED, with
>    the commit that killed it noted.
>
> **SYNTHESISED 2026-09-20** (Arthur: "collapse and synthesize the lessons into
> a smaller number — find the commonalities"). 341 separately-filed lessons
> became the rules below; not one incident was dropped, and every date, ruling,
> board arm, card, commit and file path they cited is still here, in the rule
> it belongs to. What went was the repetition: the same rule had been re-learned
> and re-filed under a new name up to eight times, which is why the file had
> grown past a one-read ceiling while getting harder, not easier, to search.
> Proved by `ops/lessons_check.py`. **Rule 3 is the change that keeps it this
> way**: the next incident of a known rule is a line in that rule's Paid-for-by
> list. A new rule is for a new failure.

---

## The sections

> **SPLIT 2026-10-04.** This file had reached 277 KB against a 160 KB
> one-read ceiling (T7.38, red 12 boards), and CLAUDE.md asks a reader to
> *"read the relevant section before touching that area"* — an instruction
> that could not be followed as written. Nothing was edited, summarised or
> dropped: each `##` section is now its own file, byte for byte, and this is
> the index. A rule is still appended the day it is learned, to the section
> where it bites.

> **SPLIT AGAIN 2026-10-09 (C551).** Section 3 had reached 182 of the corpus's
> 439 rules and 192 KB — over the same ceiling, one file. The cause was not
> that measurement is 41% of what this estate learns: section 3's ROUTING
> pattern in `ops/lessons_for.py` is `^tests/|test_|gate|invariants|board|audit`,
> which matches the thing EVERY card does, so it had become the default bucket.
> Two subjects came out of it byte for byte — **8. Reading documents** and
> **9. Counting & populations** — and a rule's `#id` is unchanged, because it is
> six hex of the claim and not a position. The honest second cause was claim
> LENGTH: the median claim in section 3 ran 449 B across claims 81–120 and
> **2,740 B across the newest twelve**, eight of which were filed in the five
> days to 2026-10-09. A section splits once; a habit of writing 2.7 KB where the
> corpus median is 780 B refills it.
>
> **The table below is GENERATED** (`ops/lessons_index.py --write`, checked by
> `--check` on the pre-push gate). It was maintained by hand until C551 and had
> rotted: it said section 3 was 99 KB when the file was 192 KB, and the corpus
> 294,000 B when it was 486,204.

**[→ lessons/INDEX.md](lessons/INDEX.md) — one line per rule, 318 of them, and
THE GREP TARGET.** Added 2026-10-06, when Arthur asked whether the rules we had
just filed were indexed well enough that the next card would find them. They
were not: sectioning by when-a-rule-bites is right, but `grep` is line-based and
a rule's claim is a bold sentence at the head of a WRAPPED paragraph — **177 of
the 318 claims cannot be found by searching the sections for the claim itself**,
and a miss reads exactly like "there is no rule about this". Search INDEX.md,
read it whole (38 KB) when you do not yet know the phrase, then open the rule at
the `file:line` it gives you for the scars. It is GENERATED
(`ops/lessons_index.py --write`) and its currency rides the pre-push doc gate;
append a rule to its SECTION, never to the index.

| Section | Read when | Claims | Size |
| --- | --- | --- | --- |
| [The recurring failure modes](lessons/0-recurring-failure-modes.md) | first, always — the shapes every other section is an instance of | 13 | 5 KB |
| [1. Ops & the estate](lessons/1-ops-the-estate.md) | touching a unit, a timer, a box, a deploy or a backup | 68 | 83 KB |
| [2. Extraction & rules](lessons/2-extraction-rules.md) | changing an extractor, a rule, a prompt or a reading | 37 | 39 KB |
| [3. Measurement & gates](lessons/3-measurement-gates.md) | writing or trusting a gate, a board arm or an instrument | 156 | 191 KB |
| [4. Capture & sources](lessons/4-capture-sources.md) | adding a source, a crawler, a fetch or a robots decision | 48 | 72 KB |
| [5. Agents & LLM lanes](lessons/5-agents-llm-lanes.md) | placing a model, a job, a card or a fleet decision | 15 | 15 KB |
| [6. Working style](lessons/6-working-style.md) | planning work, writing a card, closing one, or handing over | 81 | 69 KB |
| [7. Performance & allocation](lessons/7-performance-allocation.md) | something is slow, large, hot, or costs more than it should | 24 | 47 KB |
| [8. Reading documents](lessons/8-reading-documents.md) | reading a document — a profile, a form, a figure, what it proves | 46 | 51 KB |
| [9. Counting & populations](lessons/9-counting-populations.md) | counting — a sample, a denominator, a counter, a threshold | 37 | 59 KB |

Total 651,212 B and 525 claims across 10 files; largest 3-measurement-gates.md at 191 KB against T7.38's 160 KB one-read ceiling. GENERATED by `ops/lessons_index.py --write`.
