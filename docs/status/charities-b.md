# charities-b: where the Opus build of the charities reading stands

Session charities-b (Opus), 21 October 2026, node2. Step 4.1, the reading
half, in `registers/charities_b/`. Reads the capture's pages; fetches nothing.

## Done (merge request `charities-b`)

- `read.py`, `load.py`, `check.py`, `tables.sql`, `publish.sql`, `sample.py`,
  `sample.list`, `pane.md`, `spec.md`, the proposed profile
  `charities-odata-page` v1; 25 fast tests (2.5 s), 3 slow (2 min 18 s).
- Full build in `querynz_v4_sample.scratch_charities_b_full`: 46,131
  charities, 589,108 officers, 430,437 returns, 357 groups, 120 code
  entries; 132 rows set aside, each with its reason; every row of 1,079
  pages reconciles. Registered: 29,272 held against the register's 29,265
  (+7, within the 221 rows modified since). The register's own view agrees
  on every comparable charity. check.py green.
- Cards: the capture lands no registered count; `keys` folds a suffixed
  number. Lesson: a code list numbered apart from its rows.

## Half-done

- Nothing.

## Next

- The integrator compares this build with `charities_a` and keeps one;
  keeping this one means setting `load.KEPT`, moving it into
  `registers/charities`, and the `qv4-charities-load` job.
