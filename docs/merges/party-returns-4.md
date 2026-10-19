# party-returns-4: Part A over a page break and on attachments; party labels to registration keys
branch: session/party-returns (pushed; 8fca62c)
session: party-returns (session 4)
raised: 2026-10-20
claims: registers/party_returns/ (new `replay.py`; `schedule.py`, `donors.py`, `read.py`, `load.py`, `sample.py`, `tables.sql`, `publish.sql`, spec, pane, tests); cards: Part A updated, two label cards closed, one opened; one lesson; docs/status/party-returns.md

Step 4.1, the three items the brief named. Every change measured on all
152 landed returns, replay only, by the new
`python -m registers.party_returns.replay run|compare|shape` (its outputs
and any reading it stores go to the session's scratch, never the shared
reader store; `shape` shows a page with every name and address as `x`).

- **Part A across a page break, and what the five named returns really
  were.** ACT 2019 is a page break: a text-layer row whose figure is on
  the next page is now carried there, only when that page names nobody
  above its first figure. NZ First 2023 prints figures with no cents
  (`150000`): taken as amounts in the amount column only. Labour 2020 and
  2024 are scanner text layers that misread empty rows' numbers (`64`
  between 53 and 56): such a number is no longer a name. Labour 2024 then
  pairs every page but one figure is garbled ($7,030.16 short); Labour
  2020's page 2 has no figures in its text layer; Labour 2023's carried
  row meets a second name first and is refused. Those three need the page
  reader (carded).
- **Schedules outside the heading.** The page reader's HTML tables are
  read as rows when they carry the form's own column heading; a filer's
  own breakdown table (NZ First 2024 p4) is not, since it restates rows the
  form has. Labour 2025's 64 rows publish. National 2024's attachment
  (pages 3 to 5, 90 rows) is now read but one row's reading is truncated
  (the reader looped), $69,241.49 short: a re-read of page 3. NZ First 2021
  (both copies) and 2022 publish (no cents; `No 35000` on one line).
- **Party labels to keys.** `keys.parties.party_name(label, rows,
  on=year)` over `pub.party_names` joined to `pub.parties`. New column
  `returns.party_key` (`ADD COLUMN IF NOT EXISTS`), added at the end of
  all three views; `party` is now the registration's registered name
  (`pub.parties.name`), which is what the frozen site names. 38 of 42
  unresolved rows resolve (31 labels to 3; 114 exact, 8 core, 6 variant,
  5 fuzzy); the three left are `keys`' (card). `load` stops if
  `pub.party_names` is empty; the sample fill uses the snapshot while the
  sample's `pub` lacks it (it does today).

Result over all 152: **Part A published on 38 returns (843 rows; was 30,
679), nil 62, set aside 37 (was 45).** No name or amount already published
changed; three new names lost an address fragment against the first cut
(`Suite1`, a business park, `formerly of`). Frozen site 72 equal (was 71),
1 differs (Labour 2017, carded). Loans unchanged.

For the load: the gate's staging step adds `party_key` to `returns` and
the views gain it at their end; `pub.party_names` and `pub.parties` must
be published before this lane loads (they are, on the real database).
Please refill the sample's `pub` with the parties lane's views, so the
fast tier resolves labels the live way.

Fast tier: `registers/party_returns` green (91.9 s; the sample was not
filled: this shell has no database environment for the fill, so the
filled-sample tests did not run here). Whole repository: green in 477.7 s
before the cards were closed. A second run had two reds: `tests/test_generators.py`, because
the working copy holds the regenerated `docs/board.md` (generated files are
the integrator's; the fence refuses even restoring it, so it sits modified
and uncommitted); and `registers/companies` `test_the_outside_check_…`
at 5.4 s against the 5 s limit, outside this fence, green in the first run.

Two things for the integrator: the session's scratch folder
`/home/user/querynzv4-work/scratch/party-returns` was deleted twice
during the session by something outside it (none of the repository's
tools target it), so the replay tool now lives in the lane. And early on
I printed one donor's street address from a public return into this
session's transcript while dumping a page (hard limit 11); every later
look went through `shape`. Lesson:
`a-cause-named-in-a-card-is-a-guess-until-the-page-is-looked-at`.

## Result (integrator, 2026-10-20 10:05 NZDT)

Merged into main as 9d8e957 (merged main first; board and lessons index
regenerated; the board's catalogue took party-finance-2's two views in
this merge, since the board's real check wants a view published before
its entry). Fast tier green (355 s under load) and gate green; the gate's
load: 137 rows, 15 set aside, 843 donor rows, 10 loan rows, 14 replaced;
published. The sample's `pub` cannot carry the parties lane's views
(the fill lands lanes' inner tables under their prefixes), so the lane's
snapshot fallback stands in the sample. On the session's scratch folder:
the integrator's clean-up line for Arthur named `party-returns` while
this session ran in a new copy of that name; that was the deletion. The
hard-limit 11 note (one donor's street address printed into the
session's transcript, nowhere else) is reported to Arthur. Waiting on
Arthur: National 2022's two returns (default: neither replaced).
