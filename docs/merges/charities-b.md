# charities-b: the Opus build of the charities reading, from the shared capture
branch: session/charities-b (pushed; e7e3697)
session: charities-b (Opus)
raised: 2026-10-21
claims: registers/charities_b/ (read, load, check, capture (the listing only), tables, publish, sample, sample.list, spec, pane, README, `profile-proposed.jsonl`, tests); cards `the-charities-capture-lands-no-registered-count`, `a-charity-number-suffix-is-folded-by-the-shared-reading`; lesson `a-feed-s-code-list-can-number-its-entries-apart-from-the-rows-that-use-them`; docs/status/charities-b.md

Step 4.1, the reading half, Opus build. Reads the capture's pages from the
document store by the capture's listing (newest finished full pass, then
later changes passes; the same rule as `registers.charities.read.pages`).
Fetches nothing, imports nothing of `registers/charities`.

## Figures (full build, `querynz_v4_sample.scratch_charities_b_full`, 52 s)

| Table | Rows | Key |
| --- | --- | --- |
| charities | 46,131 (Registered 29,270, Deregistered 16,591, Removed 270) | `charities/CC12345`, the register's number as filed |
| officers | 589,108 (person 585,837, body corporate 3,271; 521 disqualified by the register's status) | `charities/officers/<OfficerId>` |
| returns | 430,437 (2,247 filed by a group alone) | `charities/returns/<AnnualReturnId>` |
| groups | 357 | the group's own number |
| codes | 120 entries of 9 code lists | |

Rows in: 1,066,285 on 1,079 pages = typed 1,066,153 + set aside 132. Every page reconciles.

Set aside, by reason:

| Set | Reason | Rows |
| --- | --- | --- |
| Organisations | no registration number | 5 |
| Organisations | the register's number is held by 2 organisations (CC65228, both registered) | 2 |
| Officers | its organisation is set aside (the two-held number) | 10 |
| Officers | no name (no person name and no body name) | 30 |
| AnnualReturn | names no organisation and no group | 61 |
| AnnualReturn | its organisation is set aside (no registration number) | 24 |

Kept but noted (`notes`): 59 NZBNs failing the check digit (left empty); 3
street-address parts holding an email address (dropped); 2 returns with
tier -1, which the code list does not hold (tier empty).

## The register's count against ours (`python -m registers.charities_b.check`: green)

- Feed's own count at each pass's start against rows landed: Organisations
  46,132 stated, 46,138 landed (the pass ran 07:29 to 23:37 on 20 October);
  Officers 589,148 = 589,148; AnnualReturn 430,522 = 430,522; Groups 357 = 357.
- Registered charities: the register said **29,265** at about 07:30 on 20
  October; we hold **29,272** (29,270 typed + the 2 set aside), **+7**, within
  the 221 organisations the register marks modified after the count. The
  capture never landed that count as a document, so the figure is a constant
  from its status file (card `the-charities-capture-lands-no-registered-count`).
- The register's own view: the names `vOrganisations` gives each charity's
  main sector, activity, beneficiary and group equal ours for all 46,121
  comparable charities (10 changed between the two captures).

## What to know

- **The feed's code lists number sectors, activities and beneficiaries
  differently from the ids the organisation rows carry** (same names, other
  ids). Decoded through the lists, 42,763 sectors were wrong. Resolved by the
  view's numbering (`read.VIEW_IDS`), each name still required to be in its
  code list; check.py and a sample test go red on a renumbering. Lesson filed.
- Address for service: the feed's street address, as the legal position's
  question 4 says (shown as the charity's address). The postal address,
  emails, phones, websites and social names are not read. Officers carry no
  address, birth date or contact detail; `ContactId` is not read (it is
  unique per row, so it is no person identifier).
- "Disqualified" is the register's own status (Disqualified, Removed as
  Disqualified). The feed's `IsNotDisqualified` is false on 3,221 rows,
  most of them Past or Qualified officers; it is kept as
  `declared_not_disqualified` and not published.
- Returns: every number on a return that is money goes to `figures` (jsonb),
  with six headline columns; head counts, hours, quantities and codes are
  left out (ruling of 14 August). Auditor, certifier and approver names and
  the performance text are not read.
- A number with a suffix (`CC…-1`, 10 charities) is kept whole;
  `keys.numbers.charity_number` would fold it (card).
- **Publishes nothing until kept:** `load.publish()` logs and returns while
  `load.KEPT` is False, so the gate's staging step cannot put both builds on
  `pub.charities`. To keep this build: set `KEPT`, move the folder into
  `registers/charities` (schema `charities_b` becomes `charities`; the
  listing in `capture.py` then reads its own lane), append
  `profile-proposed.jsonl` to `support/profiles/profiles.jsonl`, and add a
  `qv4-charities-load` job after the nightly capture.
- `capture.py` queries the capture's tables with the schema as a parameter,
  as `registers/charities/read.py` does. The one-way import test passes, but
  strictly this reads inside another lane's schema; it is the listing the
  capture's spec publishes to the two builds and goes away with the move.

## Tests

- Fast: `registers/charities_b` 25 passed in 2.5 s (`bin/fast registers/charities_b`
  green in 37 s with the sample fill: 1 s for this module, 380 rows, every hard
  case in sample.list). A mutation of the code resolution is caught by both a
  synthetic and a real-page test.
- Slow (3, marked): a full build from every captured page reconciles, meets
  the register's counts and its view, and a second full build gives the same
  rows under the same keys (hash of every table, `loaded_at` aside).
  **2 min 18 s.**
- Whole repository fast tier: one red, `tests/test_generators.py` (the board
  and lessons index, stale from my two cards and the lesson; yours to
  regenerate). 341 s against the 300 s target (recorded).

Lesson: `a-feed-s-code-list-can-number-its-entries-apart-from-the-rows-that-use-them`.

## Result (integrator, 2026-10-21 11:18 NZDT)

Merged into main as ed868ae (merged main first). Done at the merge: the
proposed profile `charities-odata-page` appended to the ledger as version
1 (73 slugs; charities-a proposes the same slug and lands as version 2);
the gate's staging load built the lane (1,066,033 rows in 54 s) and, as
the build intends, published nothing (`load.KEPT` false); the queue item
`whether-a-charity-s-address-for-service-is-shown-when-it-may-be-a-trustee-s-home`
raised with a default (withhold where the charity is not a body
corporate); board, lessons index and queue regenerated; the lesson on the
code lists' numbering indexed (240 characters). The two cards (the
suffixed charity number folded by the shared reading; the capture lands no
registered count) stand open for the keys and capture lanes.

The comparison with the Fable build (`charities-a`), made table by table
on the register's own identifiers over both full loads in the sample
database: returns agree on all 430,437 rows; this build's main sector,
activity and beneficiary match the register's own view page (46,121 of
46,121; checked against the stored `vOrganisations` page for CC10001)
where the Fable build's differ on 42,771, 33,729 and 37,755; this build's
521 disqualified officers follow the register's status where the Fable
build's 4,252 include 3,076 officers the register lists as Past or
Qualified; this build collapses the feed's doubled spaces in 252 names and
680 roles that the Fable build keeps. The lesson is filed at the
charities-a merge. This build is the one to keep: the move into
`registers/charities` (schema, publish, the `qv4-charities-load` job, the
address-for-service default) is the next charities session's work.
