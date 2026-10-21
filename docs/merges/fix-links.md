# fix-links-1: the old ledgers brought level at each build; each donation's latest live anchor applied whatever its weights version
branch: fix/links-1 (pushed; 75a4066)
session: fix-links-1 (fix, links; Opus)
raised: 2026-10-21
claims: links/old.py, links/build_all.py, links/check.py, links/spec.md, links/README.md, links/tests/test_old_ledgers.py (new), links/tests/test_review_and_old.py; cards `the-links-copy-the-old-ledgers-once-and-the-check-counts-them-live` and `the-old-estate-s-anchors-moved-to-weights-2-3-and-the-copy-calls-them-superseded` (both closed); lesson `compare-a-copy-with-its-source-at-the-copy-s-high-water-mark`

**(1) The copy is brought level at every build.** `old.copy_ledgers` reads
each ledger's `id, withdrawn_at, withdrawn_reason`, copies every row the copy
does not hold (above its highest old id, and any gap below it), and re-reads
the withdrawal on the rows held (`old.ledger_changes`). `links.build_all.run`
does copy → map → promote after the rows and links, through a third
connection on the old read-only login (`QV4_OLD_READ_URL`, already in
`v4.env`; `links.old` used it). `links.check` counts the old table up to the
copy's highest old id, withdrawals included, and reports
`decided_since_the_copy` without failing on it.

**(2) No weights version in the code.** `CURRENT_WEIGHTS` is gone. Each
donation (`source`, `row_key`) takes its latest live judgment by old id
(ids rise with `decided_at` on the live table: checked, none out of order),
never by a version sorted as text. Rows from 1.0 and 1.1 have no `row_key`
and are never the word. A hold applies while the anchors it read at its
version are still applied (the old estate's own rule: a new run is a new
read). The map's tally carries `donor_anchors_versions`: each version's
rows, live and applied, and `latest_decision_version`.

**Tests.** All six in `test_old_ledgers.py` fail against main's code. The
2.2/2.3 figures test (9,025 / 8,523 live / 6,466) fails with the version
hard-coded at 2.2 and with it hard-coded at 2.3 (both mutations run).
Dropping the withdrawal re-read fails two tests. `bin/fast links` green
(27.3 s).

**On real data, nothing live written.**
- Scratch schema `scratch_fix_links_1` (sample db): full copy of 77,180 rows
  in 3.5 s. A deliberately stale copy (newest row dropped, one withdrawal
  blanked) checked red (71,319 vs 71,319, but 501 vs 502 withdrawn). One
  build brought it level: 1 copied, 1 re-read, then green. Map 2.8 s
  (scratch has no rows, so 0 promoted).
- Old ledger, read-only: 2.3 has 6,466 rows, 6,235 applied (727 accept or
  corroborated). 2.2 has 9,025 rows, 8,523 live, 1,938 applied (35 accept or
  corroborated, on donations 2.3 has not re-judged). All 644 2.2 accept or
  corroborated decisions already promoted live agree with their 2.3
  re-judgment, so no append-only decision is contradicted. 118 of the 127
  2.2 holds no longer apply; 9 still do.
- `python -m links.check` logic on the live `links` schema, this branch's
  code, in a READ ONLY session. Old ledgers: folds 5,479 = 5,479 (325
  withdrawn each); donor_anchors 71,319 = 71,319 (502 = 502), row 75929
  decided since the copy; verdicts 381 = 381. Green. Addresses, published
  counts (links 2,815,621, groups 2,315,036, decisions 5,483) and the review
  switch are green. **Two reds, not this branch's:**
  `candidate_return_donors` 221 published vs 175 read, and
  `candidate_return_totals` 412 vs 385. candidate-returns-2 published after
  the links' 09:00 reload; the reload at this merge clears them.

**For the integrator:** reload `links` with `links.build_all`. It now copies
row 75929 (and anything newer), re-reads withdrawals, remaps and promotes on
its own; `links.old --copy` is no longer a separate step. After the reload,
`links.check` should be green on all old-ledger and candidate-returns lines.
`docs/contracts/links.md` was not touched (it says nothing about "once").
The job `qv4-links-build` needs no catalogue change.

**Left open, not carded:** decisions are append-only. If the old estate
later withdraws, or re-judges to another target, a decision already
promoted, the earlier `same` stays in `links.decisions`. It is 0 today
(above). Nothing counts it yet; a card if it ever happens.

Lesson: `lessons/compare-a-copy-with-its-source-at-the-copy-s-high-water-mark.md`.

## Result (integrator, 2026-10-21 11:55 NZDT)

Merged into main as 5193521 on the shared integrate branch `fixes-1` with
`fix-societies` and `fix-rea` (disjoint folders, one gate, merged main
first). Done at the merge: both cards closed by the fix stand with their
dates; the lesson `compare-a-copy-with-its-source-at-the-copy-s-high-water-mark`
indexed (198 characters); the gap the fix names, an applied old decision
never withdrawn when the old estate withdraws or re-judges it, carded as
`an-applied-old-decision-is-never-withdrawn-when-the-old-estate-withdraws-it`
for the lane; board, lessons index and queue regenerated. The live
`links` schema is being reloaded with this code from a detached copy of
main (started 11:58; publish and `links.check` follow), so the 727
anchors of the 2.3 round apply and the check's old-ledger count goes
green; the board restarts after it.
