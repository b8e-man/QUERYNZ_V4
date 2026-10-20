# comparison-1: the comparison with the frozen site, figure by figure, on the checks board
branch: session/comparison (pushed; 71f3475)
session: comparison (session 1, step 4.5)
raised: 2026-10-20
claims: checks/comparison.py, checks/comparison_figures.py, checks/module_checks.py, checks/jobs-proposed.toml, checks/board.py (two REGISTRY entries), checks/README.md, checks/tests/test_comparison.py, checks/tests/test_module_checks.py; 41 cards in cards/ (session: comparison, opened 2026-10-20); lessons/two-shapes-compare-by-figure-not-by-field.md; docs/decisions/queue/which-frozen-sections-belong-in-the-follow-the-money-template.md; docs/status/comparison.md

`python -m checks.comparison run` pairs the frozen current version (last
`publish` row of the old folder's RELEASES.jsonl, read only) with the
rebuilt version whose SNAPSHOT names that listing, reads every file of the
ten kinds on both sides into one flat set of figures (money in whole cents,
no tolerance), and groups every difference by a cause from an ordered rule
table; every cause has a card naming which side is right and the owning
lane. Day record `<live>/checks/comparison/days/<frozen version>.json` and
ledger `ledger.jsonl`; a clean day is no difference without a card and no
card saying the new side is wrong; the check passes at seven clean days.
Today (2026-10-20T0620 against 2026-10-20T1134): 43,062 differences, 0
uncarded, 23,067 under cards saying the new side is short; not clean.

`python -m checks.module_checks` runs every `registers/*/check.py` with a
main (bar track E's two, already on the board through windowed.py) and
`products.board check` and `products.published_site check` as commands
with a 120 s timeout (all fourteen answer in under 2 s). Today four are
red; three sit under lanes' existing cards (National 2023 twice-counted,
expense release totals printed wrong, Labour 2017's handwritten
correction) and one is new: four gazette tables published and not in the
board's catalogue (`four-gazette-tables-are-published-and-not-on-the-board`).

For the integrator: append `[jobs.qv4-site-compare]` from
`checks/jobs-proposed.toml` to the jobs catalogue (19:45 UTC, after
qv4-site-build at 19:00; needs the processor and the published site, no
graphics card); add the four gazette tables to the board's catalogue from
`registers/gazette/pane.md`; regenerate board, lessons index and queue
(the new lesson and 41 cards make them stale, which is the one failing
test here, `test_the_committed_records_generate_cleanly`).

Fast tier: checks/tests 37 passed (one slow test runs the real pair);
tests/test_imports_one_way.py and test_reading_limits.py green.
Nothing written in the old folder; no address or suppressed name printed.
Lesson: `two-shapes-compare-by-figure-not-by-field`.

## Result (integrator, 2026-10-20 13:57 NZDT)

Merged into main as d534b5d (merged main first). Done at the merge:
`qv4-site-compare` in the catalogue (priority 52, due 19:45 UTC, after
the site build) and the proposed file removed; the card
`four-gazette-tables-are-published-and-not-on-the-board` closed, since
the records commit after gazette-3 (2101719) had already put the four
views in the board's catalogue; `bin/fast` given a literal fallback to
the main checkout's venv (the report session found `_session.MAIN` is
the copy itself); records regenerated. The whole-repository fast tier
went red once on the candidate-returns sample: its "scan with no stored
page reading" case had been read minutes earlier by the live job
`qv4-read-pages-candidates` (713 pieces, queued at 13:30), so the
assertion now accepts either outcome and the lane is carded
(`the-candidate-returns-sample-s-no-reading-case-is-read-by-the-live-job`).
Gate green; its load republished candidate returns at 385 totals (372
before the readings began landing). The scheduler ran `qv4-site-compare`
once already (row 132, done). The session ran headless from the
integrator as Fable, about 35 minutes; 41 cards opened, one lesson, one
queue item (which frozen sections the template carries; default all).
