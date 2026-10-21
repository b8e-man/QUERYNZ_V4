# companies-2: company monitoring (step 5.5, ruling 19), in the companies lane
branch: session/companies-2 (pushed; 86bad8f)
session: companies-2 (Opus)
raised: 2026-10-21
claims: registers/companies/ (new `monitor.py`, `profile-proposed.jsonl`, `tests/conftest.py`, `tests/test_companies_monitor.py`; tables, publish, check, sample, sample.list, spec, pane; the lane test's fixture moved to the conftest); cards `the-companies-monitor-job-into-the-catalogue` (blocker, yours), `the-nzbn-interface-has-a-change-search-and-watchlists`; lesson `compare-two-sources-of-one-register-only-where-both-speak`; docs/status/companies.md

Step 5.5. The monthly import is untouched: `load.TABLES` and its wipe are
as they were; the monitor's tables are created by the same `tables.sql`
(`IF NOT EXISTS`) and never dropped by a load.

## The hand-off (products rule 2)

Published functions owned by the lane, not a grant on its tables:
`pub.request_company_check(nzbn, name, product) → id`,
`pub.watch_company(nzbn, product, every_days)`, `pub.unwatch_company`.
SECURITY DEFINER with a fixed search path; EXECUTE revoked from PUBLIC and
granted to `qv4_product` only; the asker is `session_user`, never an
argument. A name-only request is answered only where exactly one held
entity has that exact name; otherwise set aside asking for the NZBN.

## The monitor (`monitor.py`)

Requests oldest first, then due watches (shortest interval any product
asked; never-asked first). One call at a time to
`/gateway/nzbn/v5/entities/{nzbn}` through `fetchgate.open_url` with our
key (`db.CRED_DIR/nzbn.env`, read at use, never printed), at least 5 s
apart, at most 300 calls a NZ day, off-peak 22:00 to 01:00 NZ (before the
societies asks at 01:00, never Wednesday 21:00 to 23:00). An entity
answered earlier the same NZ day answers a request with no call. A 403,
429, 5xx or challenge stops the night and leaves the request waiting.

Each answer: landed by hash; a line in `companies.calls` (kept); read into
`lookups` (one per answer; kinds company, sole trader, partnership, trust,
society, other), `lookup_roles` (the register's role id, start and end),
`lookup_holdings` (current and historic, with `vacationDate`),
`lookup_offices` (a company's or society's REGISTERED address only);
every other address to `companies_private.lookup_addresses`; e-mail and
phone never read. Then compared with the state held before it (the last
answer, else the monthly file's current rows; a category the file lists
nothing current for is not compared) into `changes`: name, status,
director appointed / ended / not listed, holding started / ended / not
listed, registered office. Dated by the register's own date where it
states one (`date_basis` register), else the day seen. `rebuild` re-reads
every answer from the ledger.

Published: `pub.company_changes` (suppressed names blanked, row kept),
`pub.company_lookups`, `pub.company_lookup_roles` (`held_key` joins
`pub.directors`), `pub.company_lookup_holdings`.

## Proof on real lookups (8 calls, 21 October 11:05:16 to 11:05:57 NZDT)

All 200, no challenge, 5 to 6 s apart (`monitor.PROOF`, in sample.list).
Five sample companies: one change, 9429041764886 In Liquidation (August
file) → Removed; none false. 23 role rows (17 directors, 6 trustees), 5 with the register's end date.
A sole trader (name withheld by the register), a partnership (no partners
listed), a trading trust (six trustees; its two addresses private). The
slow test repeats the comparison against the real lane in `querynz_v4`:
the same one change.

## Checks

`check.py` gains `monitor_failed`, run by the same `main` and exit: every
change cites a 200 call whose bytes are in the store (the store's own path; `docs.*` is support's, so it is not queried); every
request older than 48 h answered by a landed call or set aside with a
reason; no NZ day over 300 calls. Green on the sample.

## Tests

`registers/companies/tests`: 45 (25 new), one slow. The night runs on the
filled sample with a fake transport and an in-memory store inside a
rolled-back transaction. A mutant (a trust's office published) fails a
test. Whole fast tier (347 s, over the 300 s target): one failure, `tests/test_generators.py`, because my two cards and lesson make the board and lessons index stale (generated, yours to rebuild; the test rewrote `docs/board.md` in my working copy, left uncommitted). An earlier run caught `check.py` querying `docs.*` (the docstore's); fixed, the import test green.

## For the merge, please

- Card `the-companies-monitor-job-into-the-catalogue`: the profile appended,
  the position page widened to every entity kind, `qv4-companies-monitor`
  into the catalogue.
- The publish creates the three functions; `qv4_product` must exist on both
  databases (it does on the sample).

## Result (integrator, 2026-10-21 13:37 NZDT)

Merged into main as 675415f (`merge integrate/companies-2: gate green`). Branch `integrate/companies-2` from `session/companies-2` (86bad8f), main merged twice (the second after report-3). Integrator items: profile `nzbn-entity-detail-any-kind` version 1 appended (74 slugs; the proposed file removed; the pin bumped); `qv4-companies-monitor` in `support/scheduler/jobs.toml` as specified except priority 37 (36 was `qv4-links-build`'s; the catalogue check refuses a shared priority), `support.scheduler check` green; the NZBN position page widened to every entity kind with the four answers from the status file; the blocker card closed. Fast tier green in 452.1 s (target 300 missed under load, recorded). Gate green; staging loaded the companies lane (1,920,468 entities, 139 s) and published it, which creates the monitor's tables and the three `pub.*_company*` functions. Branches and the working copy retired.
