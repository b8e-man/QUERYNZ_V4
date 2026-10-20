# charities-a: the Fable build of the charities reading, from the shared capture
branch: session/charities-a (pushed)
session: charities-a (Fable)
raised: 2026-10-21
claims: registers/charities_a/ (read, tables, load, publish, check, sample, spec, pane, capture (a note: it captures nothing), profile-proposed.jsonl, tests `test_charities_a_reading.py`, `test_charities_a_sample.py`, `test_charities_a_full.py` (slow)); lessons `a-feed-with-no-birth-date-field-still-carries-birth-dates-in-its-name-fields`, `a-charities-feed-page-is-read-by-its-own-shapes-not-its-field-names`; docs/status/charities-a.md

Step 4.1, one of the two builds of the charities lane's reading (the other,
charities_b by Opus, not read). It reads the pages the capture lane landed
(`registers/charities`: the newest finished full pass of each set and the
changes passes after it, listed in `charities.capture_pages`, bytes from the
document store by sha256) and fetches nothing. Every row is keyed by the
register's own identifier and cites its page's sha256 and its key in the
page (`place` = `OrganisationId=<n>`, `OfficerId=<n>`, `AnnualReturnId=<n>`,
`GroupId=<n>`); the lists beside an organisation come from the vOrganisations
page and cite it apart (`lists_document`).

Read, on every page the capture lists (1,158 pages, 1,142,042 rows, 5.1 GB
of JSON), into `scratch_charities_a_full` in the sample database; the load
took 69 s and the tables are 586 MB:

| Table | Rows | Notes |
| --- | --- | --- |
| charities | 46,124 | 29,263 registered, 16,591 deregistered, 270 removed; keyed `charities/CC<n>`; main codes resolved 46,124 of 46,124; lists cited on every row |
| charity_officers | 589,138 | keyed by the feed's OfficerId; 367,301 with the register's own end day; 4,254 flagged disqualified with the grounds by the feed's names; 1,756 bodies corporate; 19 with a name field withheld (`name_note`) |
| charity_returns | 430,437 | keyed by AnnualReturnId; 2,247 are a group's; tiers resolved (2 rows carry tier −1, kept unresolved); 89,796 audited, 266 with a modified opinion; 80 named figures as columns, every other non-zero figure in `figures`, 258,982 rows carry some |
| charity_groups | 357 | main codes resolved through the keyed Activities, Sectors and Beneficiaries sets |
| codes | 29,739 | every code list, keyed with the set it applies to |

Catch log, 123 lines; every page reconciles (rows = typed + set aside; the
check compares each page's row count with the capture's listing too):

| Reason | Lines |
| --- | --- |
| a return of no organisation and no group | 61 |
| return of an organisation the register's copy does not hold (the 5 blank Organisations rows) | 24 |
| charity number held by two organisation rows; the later modified one kept, the other's officers and returns attached to it | 9 |
| lists for the organisation row not kept (the same 9) | 9 |
| officer with no name (of the 5 blank rows) | 6 |
| Organisations row with no charity number (blank rows), and its vOrganisations twin | 5 + 5 |
| officer with no publishable name (every name field a date or an address) | 4 |

The register's count against the build's (`check.py`, exits 1): the feed
stated 46,132 Organisations on the first page of the pass (20 October 07:29
NZDT, `$inlinecount`, never `/$count`); the build holds 46,124, −8 (5 blank
rows, 9 duplicates, 6 rows added while the pass ran 16 hours); 221 rows
were modified during the pass, and the check passes while the difference is
within them. Registered: 29,263 held against the register's 29,265 of the
capture morning (not landed; the capture's `--measure` is the live arm).

What the reading does that the field list does not say: 15 officer name
fields held a birth date and 4 a street address (the feed publishes
neither); the field is withheld with a note and the row stays. A group's
main codes index the keyed Activities set, not the Main list. Nine charity
numbers sit on two rows. The code lists repeat an Id per EntityName. Dates
arrive as `2013-06-17T00:00:00Z`. All in the two lessons.

The one-way import rule: `registers.charities_a` may not import
`registers.charities`, so `read.py` mirrors the capture's page parser and
listing query (about 25 lines, named as mirrors). The mirrors go when the
build kept moves into `registers/charities`. `load.publish` moves nothing
(plan 4.1): the gate's staging load builds the tables and publishes none;
`publish.sql` is run against a scratch or staging schema only.

Tests: 14 fast on invented pages (keys, days, codes, the window and flags,
figures, set-asides, the sample's filter, the check's rule, the row
contract), 7 fast on the filled sample (8 charities, the hard cases by
identifier, the catch log, the views, the page reconciliation), 2 slow (the
full build, idempotent: a listing already loaded is not reloaded; the check
green). Module fast tier green in 30 s; whole-repository fast tier green in
300 s (an earlier run took 323 s, recorded). Slow tier: 69 s for the load
the first time, under a second after.

For the integrator: run this build against charities_b's tests and the
reverse; write the comparison lesson; keep one and move it to
`registers/charities` with the `charities` schema and `pub.charities`,
`pub.charity_officers`, `pub.charity_returns`; append
`charities-odata-page` to the profile ledger; install `qv4-charities-load`
to run after `qv4-charities-capture`.

For Arthur (not blocking; built on the capture's position as the default):
a small charity's address for service may be a trustee's home; it is shown
as the organisation's address, like a registered office.

## Result (integrator, 2026-10-21 11:38 NZDT)

Merged into main as 1da15d9 (merged main first; the lessons index
regenerated at the merge). Done at the merge: the proposed profile
`charities-odata-page` appended as version 2 (the Opus build's is version
1; 73 slugs); the gate's staging load built the lane (46,124 charities in
53 s) and, as the build intends, published nothing; the two lessons on
name fields and page shapes indexed (235 and 237 characters); the
comparison lesson
`prove-a-code-list-s-names-against-the-register-s-own-view` filed by the
integrator from both full loads (returns equal on all 430,437; this
build's main sector, activity and beneficiary differ from the register's
own view on 42,771, 33,729 and 37,755 charities, and its disqualified flag
reaches 3,076 officers the register lists as Past or Qualified); board,
lessons index and queue regenerated. The build kept is the Opus one
(`docs/merges/charities-b.md`); the move into `registers/charities`, with
the address-for-service default from the queue item, is `charities-3`,
launched 21 October 11:40. The question on a trustee's home as the address
for service is on the queue with that default.
