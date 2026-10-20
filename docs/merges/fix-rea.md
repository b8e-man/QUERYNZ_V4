# fix-rea: a server error from the Real Estate Authority is one failed read, not a stop
branch: fix/registers-real-estate-authority-1 (pushed; de1dd02)
session: fix-registers-real-estate-authority-1 (fix, registers/real_estate_authority; Opus)
raised: 2026-10-21
claims: registers/real_estate_authority/capture.py and its capture test; closes card `an-http-500-from-the-real-estate-authority-ends-the-run-as-failed`; lesson `a-gate-status-verdict-is-not-a-block-tell-the-server-s-own-error-from-a-challenge`

- A 500, 502, 503 or 504 whose page passes `fg.looks_challenged(200, body)`
  clean is the server's own error: set aside at stage `fetch` with its
  status, the next request waits `REST_S` (60 s) rather than the 5 s floor,
  and the run goes on. The case is not asked again in the same run and stays
  pending for the next night.
- Three failed reads in a row (server errors or transport failures) still
  stop the run, as three transport failures did before.
- A 403, a 429, or a challenge page (including one behind a 503) still
  stops the run (hard limit 6). The gate is unchanged.
- `outcome()`: a run that stopped early after landing a listing page, a
  case or a PDF records green, with "stopped early: <why>" and its counts.
  It is red only when it stopped with nothing landed.
- Also fixed on the way: a case that failed a read could be asked again
  in the same run (the pending query returned it again). The run now keeps
  a set of tried cases.

Tests: five new ones. The 500 test, the three-in-a-row test and the green
early-stop test fail against main's `capture.py` (checked).
`bin/fast registers/real_estate_authority`: green, 30.4 s. The live capture
was not run.

Not done, outside this module: other lanes that stop whenever `f.blocked` is
set will also treat a 5xx as a block. See the lesson.

## Result (integrator, 2026-10-21 11:55 NZDT)

Merged into main as 5193521 on the shared integrate branch `fixes-1` with
`fix-links` and `fix-societies` (disjoint folders, one gate, merged main
first). Done at the merge: the gate's staging reloaded and published the
lane; the card
`an-http-500-from-the-real-estate-authority-ends-the-run-as-failed` closed
by the fix stands with its date; the lesson
`a-gate-status-verdict-is-not-a-block-tell-the-server-s-own-error-from-a-challenge`
indexed (231 characters); `qv4-board` restarted; board, lessons index and
queue regenerated. The nightly `qv4-real-estate-authority-capture` at
23:00 runs the fixed code.
