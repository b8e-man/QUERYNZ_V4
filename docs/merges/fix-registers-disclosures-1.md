# fix-registers-disclosures-1: a nightly load for pub.disclosures (qv4-disclosures-load)
branch: fix/registers-disclosures-1 (pushed, 3b627ec)
session: fix-registers-disclosures-1 (scope registers/disclosures/)
raised: 2026-10-23
claims: registers/disclosures/ (load.py, check.py, spec.md, tests/test_disclosures.py); lessons/a-view-pinned-to-a-page-that-is-re-fetched-nightly-needs-a-nightly-load-before-the-build.md

## What it fixes

The integrator's finding of 23 October: the old `ec-disclosures` job rewrites
both Commission listings at 03:34 NZDT and their bytes change most nights;
pub.disclosures cites them by hash; the lane had no load job, so the 08:00
build left out 421 of 421 rows and failed the Commission gate.

- `load.stage(conn, schema, shared)`: copy the old folder's current listings
  and scans by hash (capture.copy_all), build `schema`, hold it to
  `check.verdict` (the frozen site's party-years, the forms, ruling 66).
  Green = rows read and no difference a card does not name.
- `load.job()` / `python -m registers.disclosures.load --job`: stage into
  `staging_disclosures_load` of querynz_v4, publish only on green, record
  the run (`jobrun`, job `qv4-disclosures-load`) with the frozen release it
  compared with. Red publishes nothing; the staged rows stay for a look.
- `python -m registers.disclosures.load --schema scratch_… ` runs the same
  stage on the sample database; refuses any other schema, and querynz_v4.
- `check.held` and `check.verdict` split out of `check.main` (output
  unchanged).

## Proof

- Tests: the job runs capture → build → held → verdict → publish in that
  order and reads the staged table; a difference with no card, or no row
  read, publishes nothing and records a failure. A mutant that skips the
  gate fails two of them.
- Sample database, scratch_fix_registers_disclosures_1, today's old folder:
  522 rows, 2 listings, 283 scans held, 278 linked, 0 set aside; 15
  party-years equal, 1 differs (carded); 0 differences with no card: green,
  7 s. Both cited listings are in release listing 2026-10-23T0618.
- Fast tier for the module green (85 s; the 60 s target missed, recorded).
- Not run against querynz_v4.

## The time: 18:40 UTC, not 16:30

The brief asked for 16:30 UTC (05:30 NZDT). At that hour the check compares
with the previous day's frozen release, so it goes red on every day the
Commission adds a declaration. That happened on 21 and 22 October: the
frozen site's disclosure count went 269, 270, 271. A 05:30 run would have
published nothing on two of the last three days, and the 08:00 build would
have left out every row again.

So the job has to run after the release, which ends about 06:30 local
(`current` flipped at 06:30:24 today). Old timers run on local time and
`at_utc` does not, so 18:40 UTC is 07:40 NZDT and 06:40 NZST. That is after
the release and before `qv4-site-build` (19:00 UTC) in both seasons. The NZST
margins are thin (10 min after the release, 20 before the build). The real
fix is for the job to wait on the watcher's release listing, which belongs
to the scheduler, not this lane.

## What the integrator must do

1. Run the merge gate on `fix/registers-disclosures-1` and merge on green.
2. Put this block in `support/scheduler/jobs.toml`, beside the other lanes'
   loads, and install it (qv4- prefix):

```toml
# ── disclosures (the Commission's two listings are re-fetched by the old job at 03:34 and cited by hash; load after the frozen release, before the build) ──
[jobs.qv4-disclosures-load]
description = "Disclosures: copy the old folder's current Commission listings and scanned declarations by hash, build into staging_disclosures_load, hold them to the lane's check against the frozen site, and publish pub.disclosures and pub.disclosure_items only on green. Nightly 07:40 NZDT, after the frozen release (06:15-06:30 local) and before qv4-site-build."
needs = "processor"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 600
class = "due"
priority = 38
command = ["python", "-m", "registers.disclosures.load", "--job"]
at_utc = "18:40"
nice = 10
```

3. Regenerate the job manifest and the lessons index.
4. Check the first firing: `jobrun` record `qv4-disclosures-load` says
   `published:` with the release it compared with, and the next
   `qv4-site-build` leaves out 0 disclosure rows.

## The other pinned views (asked; nothing changed)

Pages the old job rewrote at 03:34 today under `ec-donations/index/`: the
$20,000 and $30,000 tables, the by-year listing, the party register and the
logo applications.

- **party_returns**: no pinned row cites a re-fetched page. All 1,465 rows
  in its three pinned views cite the return documents (140, 53 and 7), and
  all of them are in today's listing. One catch: the lane reads the by-year
  listing, which is re-fetched nightly, for amendments (`replaced_by`, and
  `amendments.listing` holds its hash). So a new amendment shows only when
  the lane is reloaded. That is not a pin failure. It could become a card
  if `replaced_by` has to be current.
- **candidate_returns**: no. Its listing pages (`…year-2020/2023-start-N`)
  were not rewritten, and its 634 pinned rows cite returns, all in the
  listing.
- **party_finance**: not a pinned view. Its listing pages (expenses,
  promoters, financial statements) were not rewritten today.

Lesson filed (above). No card.

## Result (integrator, 2026-10-23 09:27 NZDT)

Merged with the three other fixes of the morning as `integrate/fixes-2`:
`d710863 merge integrate/fixes-2: gate green` (fast tier green in 628 s on the
integrate branch; the gate's staging step loaded and published the touched
lanes). Branches and the working copy retired. Integrator items on the
branch: the board's windowed check takes the call the board makes (with a
registry test in checks/tests), `qv4-disclosures-load` in the catalogue
(priority 84, 18:40 UTC), the compare-gate card, board and lessons index
regenerated. The worker was stopped for the window and started after the
push.
