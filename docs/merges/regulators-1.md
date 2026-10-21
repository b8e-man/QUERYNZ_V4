# regulators-1: the three step 5.3 regulator lanes (Commerce Commission, FMA, WorkSafe), all captured, none held
branch: session/regulators-1 (pushed; d3ec2ab)
session: regulators-1 (Opus)
raised: 2026-10-21
claims: registers/commerce_commission/, registers/fma/, registers/worksafe/ (each: capture, read, load, check, tables, publish, sample, sample.list, pane, spec, profile-proposed.jsonl, position/, tests); docs/status/regulators.md; one queue item (default applied); one card; three lessons

## What each lane is

- **Commerce Commission** (`pub.commerce_commission_cases`, `pub.commerce_commission_parties`). The case register:
  listing 100 a page (`:total` 1,727 on 21 October; old estate 112), each entry's Case Details read by profile
  `comcom-case-register-entry` v1: case number, kind, Act and section as stated and split per Act, status, outcome,
  dates; parties split on the Commission's '; ' only (and ' and ' between two legal names); 'Withheld' kept withheld.
  Proved on 7 entries. CC BY 4.0.
- **FMA** (`pub.fma_actions`, `pub.fma_parties`). Warnings and alerts (726; old 16) and enforcement cases (99),
  fifteen a page. Parties from the Entity Name field, else the heading before its dash, else a heading ending in a
  legal ending; topic alerts name nobody (`names_nobody`). A case's outcome is its latest timeline entry, a month
  never made a day. Address, phone, email and bank fields never read. Proved on 12 pages. CC BY 4.0.
- **WorkSafe** (`pub.worksafe_actions`, `pub.worksafe_parties`). Court summaries (608) and undertakings (62), twenty
  a page; the facts as stated: duty holder, section charged, court, plea, decision and date, fine and reparation as
  stated (a figure only where one is stated). WorkSafe's code for an unnamed defendant ('2019-A') is withheld. Facts
  in brief and incidents never read. Proved on 10 pages. Free reproduction, source acknowledged; no old figure in the
  reference note.

All three: a name withheld or stated suppressed is withheld on both views, with the heading, slug and page address;
a view shows only what the regulator lists today. No model.

## For the integrator at the merge (card `the-regulator-lanes-jobs-into-the-catalogue`)

1. Add `commerce_commission`, `fma`, `worksafe` to `support/db` `LANES`.
2. Move `registers/*/position/*.md` (three pages) to `docs/legal/positions/`.
3. Append the eight `profile-proposed.jsonl` lines to `support/profiles/profiles.jsonl`.
4. Gate floors 5 s for `www.comcom.govt.nz`, `www.fma.govt.nz`, `www.worksafe.govt.nz`.
5. Six jobs as each spec.md proposes (captures 22:30, 23:00, 23:30 nightly; loads 06:20, 06:25, 06:30).
6. Regenerate `docs/decisions/queue.md` and the lessons index: `tests/test_generators.py` is red on this branch only
   because the new queue item makes the committed queue.md stale. Everything else in the fast tier passes for these
   folders (78 lane tests, none skipped). Checks are red until a full pass is held, correctly.

## Result (integrator, 2026-10-21 21:27 NZDT)

Merged into main as cd618fd (`merge integrate/regulators-1: gate green`). Branch `integrate/regulators-1` from `session/regulators-1` (d3ec2ab), main merged. Card `the-regulator-lanes-jobs-into-the-catalogue`, now closed: `commerce_commission`, `fma` and `worksafe` in the lane list with their schemas applied with grants on both databases; the three positions moved to `docs/legal/positions/`; the eight profiles appended as version 1 (100 slugs); the three hosts floored at 5 s; six jobs in the catalogue at priorities 61 to 66 (captures 22:30, 23:00, 23:30 NZDT nightly with a four-hour budget; loads 06:20, 06:25, 06:30), `support.scheduler check` green; each lane's `load.py` gained the staging contract's `load(conn, schema)` (empty tables while no finished pass is held). The tenders board views carried with it. Fast tier green in 469.2 s. Gate green; staging: no finished pass of any listing is held in the working copy, so the six tables were made empty (0 rows each) and published; the nightly jobs fill them. The six board views go in at the next merge. The queue item on how long an action naming a person is shown carries its default. Branches and the working copy retired.
