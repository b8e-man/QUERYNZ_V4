# gazette-6: every published Gazette text cut before a street address or property reference

Branch `session/gazette-6`, on top of main at 04e824e. Scope `registers/gazette/`, plus this session's card, one
lesson and the lane's status file. Closes the card `published-gazette-titles-can-carry-a-street-address` (hard limit 15).

## What it claims

Everything was measured on every notice: all 207,133 went through this branch's load into `scratch_gazette_6_full` in
`querynz_v4_sample` (126 s; the register rows are gazette-5's read of `pub.companies`). No title or other text was printed
into the session. The work used counts and shapes made of token classes over a fixed word list.

1. **Measure.** The search covered titles, and every text column of every published view on gazette-5's uncut load.
   - Street addresses in titles: `ln` has 1,434. The card's 1,642 counted "State Highway 2 <Name> Road" as a house
     number. 29 more are spread over nine sections: `gn` 8, `al` 5, `ar` 4, `go` 4, `au` 3, `ds` 2, `sl`, `lt`, `aa`.
   - In other columns: 71 companies as printed (removals and winding-up applications whose company runs on into an
     address; all but three not joined) and 2 plaintiffs (`party`). The spec says a plaintiff's address is never held.
   - No title carries a vehicle's registration or VIN; a confiscation order's title names no vehicle.
   - No title carries a residence: no ", of <number>" after a person's name, and no "formerly of".
   - 292 company names hold an address shape ("12 Sample Street Limited"). They are the companies register's own names.
2. **Cut.** `cut.py`: `find`, `public` and `rows`.
   - It cuts at the first of three things: a house number and street, a land description (Lot/DP, Section…Block,
     record of title, Unit/Flat), or a number led by "at", "property", ", of" and the like. The words that led into it
     go with it.
   - It leaves alone a highway's or an Act's number, a date or time, and a company's name with its legal ending.
   - `read.read` runs `cut.rows` over every row of every table, so every reader and the sample share one cut. A
     possession title is cut by `possessions.public_title` first, as before. `load.build` cuts the possession names
     the join chose too.
   - The uncut value goes to the new private table `gazette_private.uncut (key, col, value)`. That includes
     possession titles, which were lost before.
   - Result: 1,463 titles cut, 4 of them to an empty title; 71 companies; 2 plaintiffs.
3. **Check.** `check.py` reads every text or array column of the lane's published tables (from
   `information_schema`, so a column added later is searched too) and fails on any value `cut.find` finds. It names
   the notice number, never the value.
   - The full load passes: `python -m registers.gazette.check --schema scratch_gazette_6_full --database
     querynz_v4_sample` exits 0, with 2,597,310 distinct values searched.
   - gazette-5's uncut load fails, exit 1: titles 1,446, companies 41 + 8, plaintiff 1.
   - New tests: cut cases (invented), the read-level cut, list columns, the check failing, and the filled sample.
     Six notices were added to `sample.list` (cut, cut to nothing, company, plaintiff, highway kept, company name
     kept). With `cut.rows` disabled, four tests fail. `bin/fast registers/gazette` is green in 55 s.
4. **Pane.** `pane.md` describes the cut and its measure. `spec.md` and the `publish.sql` comment are updated.

## Whole-repository fast tier: red, from the database

`bin/fast` (whole repository) ran 1,968 s and went red. Nearly every error was `psycopg ConnectionTimeout` in other
lanes' sample fixtures (candidate returns, companies, disclosures, …), and the windowed check's `tenancy_tribunal`
gave no answer in 120 s. Partway through the run, 10.0.0.2:5432 stopped answering (`pg_isready`: no response; the
local socket accepts). One failure was this branch's: the new lesson's rule was over the index's 240 characters. It
is fixed in 84f0324, and `tests/test_generators.py` plus the lane's tests pass without a database. The lane's own tier
with the database was green, 55 s, before the server stopped answering. Please run the gate once the server answers.

## For the integrator

- Load this lane's real tables. The new private table is owner-only by its schema's `_private` suffix, so there is
  nothing to grant.
- Lesson filed: `search-every-published-column-for-an-address-not-only-the-one-you-were-told`.
- Left alone as briefed: disciplinary findings and confiscation orders (queue, default no).

## Result (integrator, 2026-10-21 10:10 NZDT)

Merged into main as 3a032ec (merged main first). Done at the merge: the
live `gazette` schema reloaded by the gate (207,133 notices, 121 s) and
published with the cut; `python -m registers.gazette.check` on the live
tables exits 0 (every published text column searched, nothing found);
`qv4-board` restarted; board, lessons index and queue regenerated. No
catalogue or profile change. The new private table `gazette_private.uncut`
stays owner-only by its suffix. The lesson
`search-every-published-column-for-an-address-not-only-the-one-you-were-told`
is in the index (rule 217 characters). Disciplinary findings and
confiscation orders stay on the queue (default no). The whole-repository
red the request reports was the cable outage of 07:50 to 08:57; the gate
ran with the link restored and was green first time.
