# charities-3: the Opus build kept, moved into the charities lane
branch: session/charities-3 (pushed; b787e81)
session: charities-3 (Opus)
raised: 2026-10-21
claims: registers/charities/ (capture, read, load, check, tables, publish, sample, sample.list, pane, spec, profile-proposed.jsonl, tests); registers/charities_a/ and registers/charities_b/ deleted; docs/status/charities.md (charities-a.md and charities-b.md folded in and deleted)

Step 4.1, the keep: `registers/charities_b` (Opus) moved into the capture's
folder as one lane. Nothing outside the three lane folders and the status
file is edited; what needs the integrator is listed below.

## What the lane is now

- **One schema.** `charities` holds the capture's record (`capture_passes`,
  `capture_pages`, `capture_set_aside`; never dropped) and the reading's
  tables (`charities`, `officers`, `returns`, `groups`, `codes`, the ledger
  `read_pages`, the catch log `read_set_aside`, `read_notes`), dropped and
  rebuilt by `load.py` only. `charities_private.addresses` holds each
  charity's address for service. `tables.sql` is one file in two parts; the
  capture makes the first, the load the second.
- **The listing from the lane's own tables:** `read.pages` (no mirror; the
  build's `capture.py` copy is gone).
- **Publish:** `load.publish(conn, staging)` moves the reading into
  `charities`/`charities_private` and runs publish.sql in one transaction;
  `pub.charities`, `pub.charity_officers`, `pub.charity_returns`, each row
  with document, page, place, reader, profile and version.
- **The queue item's default** (`whether-a-charity-s-address-for-service-...`):
  the address goes to `charities_private` and `pub.charities` shows it only
  where `legal_structure` is Incorporated Society, Company, or Charitable
  Trusts incorporated under the Charitable Trusts Act. Full copy: 25,864
  charities shown an address; 20,031 withheld: 3,524 of the other
  structures and 16,507 that file no legal structure at all (15,580 of
  those deregistered, 963 registered). The rule
  is one list in publish.sql; a test each way, on invented rows and on six
  real charities of six structures.
- **Officers:** no address, birth date or contact column anywhere; a
  `suppressed` column (false as read: the feed carries no suppression marker,
  the register leaves restricted officers out) blanked on the view, row kept,
  tested; a name field holding a date or an address withheld with
  `name_note` (the Fable build's two findings, as tests and four real sample
  cases): 15 dates and 4 addresses on the full copy, no row lost. Three body
  names "<digits> Limited" and one seven-digit-led body name are company
  names and are kept (a legal ending, or more than four digits, is no street
  number).
- **check.py** (exit 1 on any): the capture's measure, live (two counts
  through the gate), judged within the rows the register moved; the
  reading's reconciliation; the registered count on the capture day; the
  register's view agreeing on every charity; no officer name column holding
  a date or an address. `--offline` leaves out the two requests.

## Two capture fixes found on the way

1. **The feed compares a `datetime` literal as UTC.** `capture.odata_datetime`
   wrote NZ local time, so a changes pass asked from 13 hours later than it
   meant; the one-day overlap hid it. Measured 21 October: `ModifiedOn ge
   datetime'2026-10-20T06:00:00'` counted 1, `'2026-10-19T19:00:00'` 228; the
   held rows' last change is 06:02 UTC. Now UTC; tests updated.
2. **The registered count lands** with each full pass of Organisations
   (`Organisations:Registered`, a one-page pass, the count in `stated`): one
   request a month. The check prefers it, else the 20 October figure.

## Figures (full build from every captured page, `querynz_v4_sample.scratch_charities_full`)

46,131 charities, 45,895 addresses (private), 589,108 officers, 430,437
returns, 357 groups, 120 codes; 1,066,285 rows on 1,079 pages = typed +
132 set aside, every page reconciles; 60 s, 0.26 GB peak. The same counts
as the charities_b build. check.py green: registered 29,272 held against
the register's 29,265 on the capture day (+7, within the 221 modified
after); the register's view agrees on 46,121 of 46,121 compared (10 moved);
no name faults left; live measure 29,272 held = 29,272 now (230 moved since
the pass began).

## Tests

- Lane fast: 57 passed (4 s); `bin/fast registers/charities` green in 32 s.
- Whole repository fast tier (`bin/fast`): green in 405 s; the 300 s target missed (recorded by the tier).
- Slow (4, marked): green in 2 min 42 s: a full build from every captured page reconciles every row; it meets the register's counts and its view, with no name fault left; a second full build gives the same rows under the same keys; the capture's measure holds live.

## For the integrator

1. **Job** `qv4-charities-load` into `support/scheduler/jobs.toml` (spec.md's
   jobs line): nightly 06:30 NZDT (`at_utc = "17:30"`), `needs = "processor"`,
   `memory_gb = 0.5`, `deadline_s = 1800`, `query_timeout_s = 600`, `nice = 10`,
   a free priority, `command = ["python", "-m", "registers.charities.load", "--job"]`.
   It loads nothing when the listing equals what was last published; otherwise
   builds in `staging_charities_load` of querynz_v4, checks, publishes on green.
   The gate's staging step publishes too (`load.publish`), so the views exist
   from the merge.
2. **Profile:** append `registers/charities/profile-proposed.jsonl` to
   `support/profiles/profiles.jsonl` as `charities-odata-page` version 3 (the
   rows cite v3; tooling now `registers/charities/read.py`).
3. **Board views** (products/board catalogue), fields as pane.md names them:
   *Charities* (`pub.charities`), *Charity officers* (`pub.charity_officers`:
   names, `role`, `started_on`, `ended_on`, `status`, `disqualified`,
   `name_note`; suppression column `suppressed`; no address field exists to
   add), *Charity returns* (`pub.charity_returns`).
4. **Cards:** close `the-charities-capture-lands-no-registered-count` with:
   "Closed by charities-3: `capture.Run.registered()` lands the register's
   count with each full pass of Organisations as a one-page pass
   (`Organisations:Registered`); `check.py` holds the reading to it, falling
   back to the 20 October figure for an older pass. First real landing at the
   next full copy, about 17 November 2026." Leave
   `a-charity-number-suffix-is-folded-by-the-shared-reading` open for `keys`
   (the lane keys on the number as filed; nothing published depends on the
   fold).
5. **Lesson** (the fence kept me out of `lessons/`; please file as
   `lessons/an-odata-feed-s-datetime-literal-is-its-stored-clock-not-the-register-s.md`):
   "Ask an OData feed for one known moment before trusting its datetime
   literal: the Charities feed compares `datetime'…'` as UTC, the capture
   wrote NZ local, and a one-day overlap hid the 13-hour shift until a count
   of 0 had to be proved able to be non-zero." area: charities, capture,
   OData, dates, checks that silently pass. paid-for-by: 2026-10-21,
   charities-3.
   The lesson `a-feed-with-no-birth-date-field-...` names
   `registers/charities_a/read.py name_fault`; it is now
   `registers/charities/read.py name_fault`.
6. **Scratch schemas for Arthur to drop** (sample database; not dropped by
   me): `scratch_charities_a`, `scratch_charities_a_full`,
   `scratch_charities_a_private`, `scratch_charities_a_test`,
   `scratch_charities_b`, `scratch_charities_b_full`,
   `scratch_charities_b_private`, `scratch_charities_b_slow`. This session's
   own: `scratch_charities_full`, `scratch_charities_slow`,
   `scratch_charities_lane`, `scratch_charities_lane_private`,
   `scratch_charities_3`, `scratch_charities_3_private`.

## Waits on Arthur

- The address-for-service ruling (queue item above): built on the default;
  flipping it is the one list in publish.sql.

## Result (integrator, 2026-10-21 14:25 NZDT)

Merged into main as 1d5520a (`merge integrate/charities-3: gate green`). Branch `integrate/charities-3` from `session/charities-3` (b787e81), main merged. Integrator items: `qv4-charities-load` in the catalogue (priority 38, free; `support.scheduler check` green); `charities-odata-page` version 3 appended, the proposed file removed, the lane's profile-version test now reads the ledger once the file is gone; the OData datetime lesson filed (240 characters) and the birth-date lesson's path corrected; the registered-count card closed with the text given. Rulings 75 to 77 recorded on this branch; the three links queue items closed into `cards/the-links-structure-questions-are-tried-after-the-build.md`; a card for the report shape's and templates' stale charities flags. Fast tier red once (the profile test), then green in 315.7 s. Gate red twice: first the three charities board views named before staging published the lane (`pub.charities missing`), then the board's live check red on companies-2's four lookup views with no catalogue entry; the charities views wait for the next merge (lesson drafted), the four companies views are catalogued here. Third gate green; staging loaded 1,066,033 rows in 49 s and published `pub.charities`, `pub.charity_officers`, `pub.charity_returns`. `qv4-board` restarted 14:27. Branches and the working copy retired; the scratch schemas `scratch_charities_3` and `scratch_charities_3_private` are Arthur's to drop.
