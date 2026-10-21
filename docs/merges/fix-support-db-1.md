# fix-support-db-1: the owner login on querynz_v4 is refused to an unmarked session
branch: fix/support-db-1 (pushed; dfc0b05)
session: fix-support-db-1 (fix, support/db/)
raised: 2026-10-22
claims: support/db/__init__.py (`guard`, `marked`, `LiveRefused`, called first in `connect`), support/db/tests/test_db.py (five new tests); cards/a-lanes-job-path-published-live-from-a-session-before-the-gate.md (closed); cards/the-green-party-s-2026-disclosures-moved-on-the-22-october-release.md (new finding); lessons/a-mark-a-brief-names-is-checked-against-every-caller-s-real-environment.md; docs/decisions/queue/whether-every-live-writer-carries-a-mark-or-only-a-session-needs-one.md

## What the integrator must do

Export `QV4_INTEGRATOR=1` in the shell that runs the merge gate and every
hand run on `querynz_v4` (the installer, the scheduler's catalogue
commands, `python -m support.db apply|check`, a lane's `load --job` by
hand), **before you run the gate on this branch**. Nothing else changes.
Without it the gate's own slow tests and its staging load are refused,
because the integrator is a session.

## What changed

`db.connect` raises `LiveRefused` before psycopg is imported when all of
these hold: the key is the owner's, the database is `querynz_v4` (named, or
read from the URL when none is named), the process is inside a Claude
session (`CLAUDECODE` set), and it has no mark (`QV4_PIECE` or `QV4_RUN_ID`
non-empty, or `QV4_INTEGRATOR=1`). The message is one sentence: a session
proves a load in its scratch schema in `querynz_v4_sample` only; the live
tables are written by the scheduler and the merge gate.

**One departure from the brief, and why.** The brief asked to refuse every
unmarked caller. That would have stopped the scheduler at its next
restart: none of the nine installed units (`~/.config/systemd/user/qv4-*`)
carries a mark, the worker daemon opens the owner login on `querynz_v4`
itself, and `worker._env` sets `QV4_PIECE` only on pieced jobs, so every
lane's `load --job` and capture runs without it. systemd's `INVOCATION_ID`
cannot be the mark either, because a session's terminal carries it too. So
the refusal applies only inside a session, and `QV4_RUN_ID` (set on every
job) is accepted beside `QV4_PIECE`. The stricter rule needs an installer
change, so it is in the decision queue with this as its default.

Proved on the real credentials from this session: the owner login on
`querynz_v4` was refused with that sentence; the owner login on
`querynz_v4_sample` and the reader on `querynz_v4` both connected.

## Every owner connection to querynz_v4: who runs it, and whether it passes

Nothing below was changed. "Unit" means not a session, so it passes
without a mark. "Job" means the worker's child, which also carries
`QV4_RUN_ID`.

| Caller | Run by | Passes because |
| --- | --- | --- |
| `support/scheduler/worker.py` `_connect` (the worker daemon) | unit `qv4-worker@` | unit |
| `registers/*/load.py --job` (charities, party_boards, limited_partnerships, building_practitioners, tenders, commerce_commission, fma, worksafe, overseas_investment, grants) | job, unpieced | job (`QV4_RUN_ID`); refused from a session |
| `registers/{openlaw,sanctions,hdc_decisions}/load.py --job` | not catalogued: integrator by hand, or gate staging via `publish` | `QV4_INTEGRATOR=1` |
| `registers/*/load.py` `publish` through `support/staging` | merge gate subprocess | inherits `QV4_INTEGRATOR=1` |
| `registers/*/capture.py` (`--database` default; charities, societies, courts, tenancy_tribunal, real_estate_authority, limited_partnerships, building_practitioners, tenders, commerce_commission, fma, worksafe, overseas_investment, grants) | job, unpieced; openlaw, hdc_decisions, sanctions captures are not catalogued (integrator by hand) | job, or `QV4_INTEGRATOR=1` |
| `registers/societies/capture.py:453` | job `qv4-societies-capture` | job |
| `registers/companies/monitor.py:726,730` | job `qv4-companies-monitor` | job |
| `registers/courts/suppress.py`, `registers/openlaw/check.py`, `registers/courts/check.py` (owner when shared) | hand runs | `QV4_INTEGRATOR=1`; refused from a session |
| `links/build_all.py` | job `qv4-links-build` | job |
| `links/review.py` | job `qv4-links-review` | job |
| `links/rows.py`, `links/build.py`, `links/pairs.py`, `links/measure.py`, `links/old.py`, `links/check.py` | hand runs (no scratch option: database fixed to `querynz_v4`) | `QV4_INTEGRATOR=1`; a links session can no longer run them |
| `support/trials/piece.py` | jobs `qv4-trial-read-*`, pieced | job |
| `support/trials/queue.py`, `support/trials/score.py` | trial session or integrator by hand | `QV4_INTEGRATOR=1` |
| `support/installer` | integrator | `QV4_INTEGRATOR=1` |
| `support/scheduler/__main__.py` `_conn` (tables, status, report, enqueue, cancel, reread-piece, read-pages, embed-piece) | jobs for the pieces; integrator for the catalogue commands | job, or `QV4_INTEGRATOR=1` |
| `support/staging` | merge gate subprocess | inherits `QV4_INTEGRATOR=1` |
| `support/offsite/copy.py` | unit `qv4-offsite-dump`, job `qv4-offsite-copy` | unit / job (`copy.py:374` reads `db.url` for pg_dump, not `connect`, and is not guarded) |
| `products/{board,report,scan}` `state_connect` (state default `querynz_v4/<schema>`) | units `qv4-board`, `qv4-report`, `qv4-scan`; job `qv4-scan-rerun` | unit / job; refused from a session unless `QV4_*_STATE` points at the sample |
| `support/db` `apply`, `check` | integrator / founding | `QV4_INTEGRATOR=1` |

Sessions the plan allows to touch live things (scheduler, trial, track
sessions with their own jobs) are now refused on `enqueue`/`cancel` as
well. At the default their brief exports `QV4_INTEGRATOR=1` for those
commands (decision queue item).

## Checks

- `bin/fast support/db`: green, 40.3 s (12 run, 7 new cases in five tests: the refusal
  without a mark and before psycopg; the default database read from the
  URL; the pass with each of the three marks; an installed unit passing;
  the sample database and both reader logins never refused).
- Repository-wide `bin/fast`: one red, 596 s (target 300 s missed,
  recorded). `registers/disclosures/tests/test_disclosures.py::test_each_party_year_equals_the_frozen_site_or_has_a_card`:
  The Green Party of Aotearoa New Zealand 2026, ours 496,694.56, frozen
  524,208.56. The frozen figures file was rewritten by this morning's
  release (06:16). Nothing to do with this change: no `LiveRefused` in the
  log, and the lane connects to the sample. Carded
  (`the-green-party-s-2026-disclosures-moved-on-the-22-october-release`).
  The card satisfies the test's first assertion, but its floor (`>= 14`
  equal party-years, line 385) now finds 13. Lowering it to 13 is outside
  this fence, so **every branch's gate run is red on it until the
  disclosures lane, or you, lower it**, as was done for ACT 2026 on 21
  October.

Lesson: `a-mark-a-brief-names-is-checked-against-every-caller-s-real-environment`.

## Result (integrator, 2026-10-22 07:33 NZDT)

Merged into main as a18c966 (`merge integrate/fix-support-db-1: gate green`). Branch `integrate/fix-support-db-1` from `fix/support-db-1` (dfc0b05), main merged. Integrator items: the disclosures floor 14 to 13 while the Green Party 2026 figure that moved on the 22 October release is carded (the session's card); the new queue item's two explanatory lines moved below its header so the queue generates (the one fast-tier red, 591 s). The departure from the brief accepted: the refusal applies inside a session only, QV4_RUN_ID accepted beside QV4_PIECE; the stricter rule stays on the queue at the default. From here the integrator exports QV4_INTEGRATOR=1 for the gate and every hand run on querynz_v4. Gate green; staging reloaded disclosures (522 rows). Branches and the working copy retired.
