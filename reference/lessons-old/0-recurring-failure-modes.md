> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## The recurring failure modes

Most rules below are instances of a few modes. When something is wrong and you
don't know where to look, start here.

1. **"The thing I changed is not the thing that ran."** Stale processes, stale
   checkouts, timers that fired before the sync, verification at the wrong
   layer.
2. **"Green is not throughput."** A job that runs on time, exits 0 and moves
   nothing: filters that match no rows, empty reference tables, skip-lists
   without status, done-signals blind to absent rows.
3. **"The instrument is lying."** Scores that move because the grader changed,
   metrics that rank two populations interleaved, single LLM runs treated as
   measurements, caps that silently truncate.
4. **"The wrong answer teaches itself."** Auto-executed verdicts whose
   artifacts route future work — merges that add aliases, labels that scope the
   cleanup delete, coverage rules that manufacture evidence.
5. **"Name shape is not identity."** Similarity, containment, transitive
   neighbours and NER labels all propose; only evidence, IDs or corroboration
   decide.
6. **"The cheap probe you skipped."** Blast radius, EXPLAIN, a labelled sample,
   an ambiguity count — minutes of measurement that would have replaced hours
   of building or a wrong diagnosis.
7. **"The verification ran inside the window."** A fix to state that something
   else rewrites on a cycle, checked before one cycle has passed: an RTC read
   back four minutes after a change that a kernel overwrites every eleven
   (2026-09-19). Ask what else writes this, and on what period, before reading
   it back.
8. **"Measured alone, wrong together."** A setting measured-good in isolation
   and inverted under concurrent load: a 20 GB prompt cache that was fine while
   extraction idled and fatal when it ran; a 4× speculative-decoding win that
   fell inside baseline noise at fleet concurrency. (2026-08-22)
9. **"The green that means we did not look."** A verdict of *checked and found
   nothing* returned over inputs that were never fetched: flags reading `clear`
   from an assembly the register outage left empty (2026-09-19), a report whose
   verdict was `worst or "clear"` so that every-check-blocked printed green.
   The tell is a negative verdict that needs no evidence to be constructed: a
   `fired` flag must cite, a `clear` need only name a scope, so the cheapest
   thing to emit is the reassuring one. Ask of every green: what would this
   have looked like if the source had been unreachable?

10. **"The counter is a witness nobody calls."** A table's id sequence,
   burn rate, or high-water mark states plainly that rows are churning, long
   before any output looks wrong. 10,662 rows whose sequence had reached
   513,595 said "these rows are deleted and re-inserted" for a month while
   every count, every spot-check and every page looked right (2026-09-21).
   When a derived table misbehaves, compare `max(id)` to `count(*)` first: it
   is one query and it distinguishes rewritten from appended.

11. **"The check is adjacent to the question it claims to answer."** A
   measurement of the thing NEXT TO the thing that matters, reading green for
   as long as the two happen to agree. Not a missing check and not a broken
   one — a check of a neighbour: swap FULLNESS for memory pressure, free RAM
   for free connections, embeds for refusals, the last phase WRITTEN for the
   phase that RAN, "a database answered" for WHICH database, "it ran last
   night" for "it will run tonight", a median over all days for the median of
   that WEEKDAY, the card's prose for the card's STATUS cell, the gate's last
   line (its tally) for the gate's failure lines, prose saying "append-only"
   for anything enforcing it. **Fifteen instances in one session (2026-10-05,
   C500/C507/C508/C509/C510/C041/C037/C034/C061/C059/C112/C457/C016/C017 and
   my own `test_all_covers_every_suite`)** — the estate's characteristic
   failure, and the reason to ask of any green not "did it pass" but **what
   exactly did that measure.** It survives review because the neighbour is
   genuinely correlated: 96% swap usually does accompany thrashing, a fleet
   that fits in RAM usually fits in connections. The tell is that the check's
   own words and the question's words are different nouns.

- **A per-cent sign inside a SQL COMMENT is still scanned for placeholders.**
  psycopg refuses a parameterised statement whose text contains `%` followed
  by anything but s, b or t — comments included. A comment written to explain
  why the query avoided a LIKE pattern broke the query by quoting the pattern.
  (`healer/reread.py`, 2026-09-21.)

- **A shared SQL fragment that ENDS in a `--` comment swallows whatever you
  append on that line.** `v3.eligibility.ELIGIBLE` ends
  `… IS DISTINCT FROM 'duplicate'    -- L1591: …`, so interpolating it inside a
  `NOT ( … )` and closing the paren on the same line put the `)` inside the
  comment: postgres saw an unclosed `NOT (`. Put the paren on its own line.
  Sibling of the per-cent sign above, and found the same way — by running it.
  (`news/reconcile_ledger.py`, C555, 2026-10-09.)
