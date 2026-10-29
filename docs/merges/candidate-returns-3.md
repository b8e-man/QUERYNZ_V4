# candidate-returns-3: the Commission's spreadsheet rows published where no return is read
branch: session/candidate-returns-3 (pushed; b0537c4)
session: candidate-returns-3 (Opus, node2)
raised: 2026-10-30
claims: registers/candidate_returns/ (`publish.sql`, `commission.py`, `load.py`, `tables.sql`, `spec.md`, `pane.md`, tests); card `electorate-money-waits-on-the-candidate-returns-lane` (annotated, owner now site); lesson `measure-a-view-change-on-the-site-by-putting-its-select-in-the-build-s-reads`; docs/status/candidate-returns.md

No model called, no document read, nothing fetched, nothing queued live.

- `pub.candidate_return_totals` gains, after the read returns, one row per
  row of the Commission's newest summary spreadsheet with figures that no
  read current or unlisted return is placed on (`files.sheet_key`): 675 on
  the live tables (2020 363, 2023 312). `read_from` 'commission' tells it
  apart (pane.md says so); the return's own columns are NULL; the
  Commission's donations, expenses and (2023) loans stand in
  `commission_donations`, `commission_expenses`, `commission_loans`, the
  columns the template already takes as the headline. Key: the
  Commission row's own `<spreadsheet sha256>/<row>` (never
  `/declaration`). Citation: `document` is the spreadsheet's hash,
  `place` "sheet <tab>, row <n>", and two new columns at the view's end,
  `sheet` and `sheet_row`. "Return not received" rows (15) not published.
- The replacement rule is in `publish.sql`: a spreadsheet row is withdrawn
  once a current or unlisted return placed on it has been read; a
  replaced return read does not cover it. Tested by withdrawing and
  re-adding a read return in the sample.
- `commission.sheet` (new column, ALTER ADD IF NOT EXISTS): the workbook
  tab, through the workbook's relationships. The catch log and the
  outside check are unchanged.
- Tests (sample, which holds both real spreadsheets whole, 1,095 rows):
  5 new and 1 changed; 5 fail on main's code and pass here (the
  no-candidate-has-both guard holds trivially on main); lane fast tier green; whole-repository fast tier green except its time (764 s against the 300 s target, recorded).

Measured against the frozen 2026-10-29T0616, base (main's view) and
branch both built in scratch from the same listing, `checks.comparison`
unedited; the base reproduced the day file's 5,133:
candidate-returns-not-held 5,133 → 3,189 (electorate 776 → 3, electorates
206 → 2, home 627 → 311, subject 1,570 → 919, donor 1,412 and pickers 542
unchanged); rebuilt-side-wrong 7,216 → 5,280; total 29,186 → 28,619;
uncarded 0. `cite-key` +675 (one citation file per new row) and
`nil-return-is-a-zero` +740 (the Commission's NIL as $0.00, rebuilt side
ruled right) rose. What remains: donor pages, pickers and person pages'
donations received wait on Part A from the scans' readings (ruling 79);
the home race totals carry 2017 and frozen party labels; Christchurch
Central 2020's two Webbs.

For the integrator: other readers of the view see 675 new rows. The site
reads them through the headline columns as designed, but `render.cites`
labels them "EC candidate return (declaration)" and writes "donations
$0.00" from the empty return columns (noted on the card for site). The
links' `rows.py` reads every row with a surname, so it gains 675 candidate
rows; board shows them with the return's columns empty. Proposed job
`qv4-candidate-returns-load` in spec.md; nothing installed.

## Result

Merged 30 October 2026, 08:58, as 402dd42 (integrate branch 3867ec2; gate green, marked, staging loaded and published
in 95 s). Two integrator commits on the way: the load module's command-line entry `python -m registers.candidate_returns.load`
(stage, then publish; `--schema` for a scratch proof) for the nightly job `qv4-candidate-returns-load`, with a test; and the
Commission arm's NULL figures typed `numeric(14,2)`, because the first gate refused the untyped NULL ("cannot change data
type of view column donations from numeric(14,2) to numeric": a union takes the looser type and the published view already
existed). Published: 675 Commission rows ($5.58 M of donations) beside 413 read returns (351 text, 62 pixels). The 4.5 cause
"candidate returns not held" measured 5,133 → 3,189 on the session's own run. The nightly job's line goes into
`support/scheduler/jobs.toml` with the support follow-up branch.
