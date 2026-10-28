# fix-links-3: ruling 114, the eight people views and the organisation rules on four registers
branch: fix/links-1 (pushed, 1ce26f3; three commits on main's 957bfd6; main has moved to ecc101a with no change under links/)
session: fix-links-1 (Opus, fix weight, scope links/)
raised: 2026-10-28
claims: links/ (rows.py, rules.py, build.py, check.py, measure.py, tables.sql, spec.md, README.md, measurements.md, tests/test_people_views.py new, tests/test_bodies.py new, tests/test_rules.py); cards/three-test-pair-kinds-the-registers-cannot-supply.md (added to, still open); one lesson, lessons/INDEX.md; docs/status/links.md
publish.sql: **unchanged**. tables.sql: one new table, `links.bodies` (made by `links.ddl()` at the job's first step; no `publish_ddl()` needed).
job after the merge: queue `qv4-links-build`, then `python -m links.check` live (items 4 and 9), and read the run's `peak_mb`.

## How this was proved

A session may no longer write the live database (the owner login is
refused there) and the sample database publishes none of the views the rows
read, so no scratch build was possible on either. Proved instead: (1) the
new code run read-only over the live published views through the read
login, nothing written (the figures below); (2) the build step, check item
9 and measurement 10 on the real engine in a rolled-back schema of the
sample database, with planted faults; (3) the live rows through each new
source's own SQL in slow tests. `QV4_INTEGRATOR=1 bin/fast links`: green
(43 s). All of `links/tests`, slow included: pass. Root fast tests: pass
(`tests/test_generators.py` failed once on a first run and passed twice
after; it does not touch links/). `bin/fast` regenerates `docs/board.md`
in the working copy; the hook keeps it out of the commit.

## Part 1, people

`rows.SOURCES` gains the eight views, each with its dates, document,
suppressed flag and name parts as the existing sources have them:

| View | Register (ref) | Name read from | Entity | Dates |
| --- | --- | --- | --- | --- |
| charity_officers, `kind = 'person'` | charities | first, middle, last_name | `charities:` charity_key | started_on, ended_on |
| gazette_celebrants | gazette | given_names, surname (parts) | none (organisation is text) | period_from or published_on, period_to |
| gazette_practitioners | gazette | name | none | published_on |
| limited_partnership_partners, `kind = 'person'` | limited_partnerships | first, middle_names, last_name | `limited_partnerships:` partnership_key | started_on, ended_on |
| party_board_roles | party_boards | name | `parties:` party | captured_on, last_captured_on |
| local_election_returns | local_elections | candidate_as_listed | none | the election year |
| building_practitioner_decisions | building_practitioners | name (its `suppressed`) | none | decided_on |
| councillor_interests | councillor_interests | member | none | none (`as_at` is blank on all 56) |

A partner or officer that is a body is told by the view's own `kind`
column and not read (3,573 partners, 3,271 officers). Local candidates and
councillors are politician rows (near by name, never confirmed), as MPs and
candidates are: my judgment from the design's rule for candidates; say if
it should be otherwise.

**The set-aside.** The brief said rows.py already gives a bare initial no
key. It did not: it set aside suppressed, withheld and blank names only
("J." was keyed `j`). It now also sets aside a bare initial and a name with
nothing outside brackets (three local rows filed "(combined)"). On live,
no row of the 19 existing views is set aside by it.

**Live, read-only:** rows 2,861,853 → 3,619,802 (+757,949); name keys
1,010,393 → 1,339,246 (+328,853). Every new row's ref is unique and none
meets an existing ref.

| View | Read | Written | Set aside | Name keys | Near pairs it adds | Full-name links it adds |
| --- | --- | --- | --- | --- | --- | --- |
| charity_officers | 586,095 | 586,095 | 0 | 424,218 | 259,520 | 124,072 |
| gazette_celebrants | 159,502 | 159,502 | 0 | 37,678 | 104,634 | 35,787 |
| gazette_practitioners | 6,045 | 6,045 | 0 | 687 | 2,261 | 3,681 |
| party_board_roles | 2,876 | 2,876 | 0 | 116 | 2,850 | 8 |
| local_election_returns | 1,979 | 1,976 | 3 no name | 1,560 | 1,134 | 0 |
| building_practitioner_decisions | 264 | 261 | 3 suppressed | 224 | 173 | 14 |
| limited_partnership_partners | 139 | 139 | 0 | 126 | 38 | 49 |
| councillor_interests | 56 | 56 | 0 | 15 | 51 | 0 |
| all eight | | 757,949 | | | 373,477 | 166,841 |

Near and full-name figures are estimates against the live groups, each view
alone; measurement 10 counts them from the tables after the build. Party
board roles are one row per captured page (116 names, 2,850 near pairs).

**The board's fallback.** `products/board/collapse.py` `row_name_keys`
keys a row `pub.names` lacks, by `<register>:<key>`. The lane's refs for
all eight views use the board catalogue's registers, so after the build
`pub.names` holds these rows and the fallback is not reached for them. The
two keys agree on live rows: `links/tests/test_people_views.py` copies the
fold (links may not import products) and compares it with the lane's keys
on 400 live celebrant and 400 live charity officer rows, through each
source's own SQL: all agree. Mutation: swapping a celebrant's surname and
given names in the source SQL turns the celebrant test red (run and
restored).

## Part 2, organisations

`organisation-sole-company@2` and `organisation-one-live-company@2`
(`rules.sole_body`, `build.body_links`) replace @1 in the build. @1 is
unchanged in `rules.py` (`rules.RETIRED`) so a stored @1 link reads as it
meant. Near stays `organisation-name@1`, its reason now naming the
registers that hold the name ("a name match on the companies and
incorporated societies registers; …"). Bodies are read into
`links.bodies` from all of `pub.companies`, `pub.societies`,
`pub.limited_partnerships` and `pub.charities`, each with its own dates
(charities: registered and deregistered; a re-registered charity is not
removed). A status of removed with no published date makes the body's
liveness unknown: it never confirms and blocks another of its name.

**One body counted once.** `pub.companies` already holds every society
and every limited partnership (register `other_incorporated`: 53,271 of
53,271 and 3,380 of 3,380 by NZBN, the same number and dates), and @1 read
them all. The charities register carries an NZBN on 29,928 charities
(29,384 a Companies Office body) and an incorporation number (the company,
society or trust board number; agreeing with the NZBN on 26,893). A body
is folded onto its Companies Office row by NZBN, else, for a charity, by
that number where its legal structure names that register and the number
is one row there: 31,532 of 46,139 charities fold, 14,607 stand alone. A
body's liveness takes the formation registers (companies, societies,
partnerships) where it has one, else its charity row.

**Live, read-only: the same 292 donation rows confirm, the same 292
pairs as @1; none new, none lost.** 262 `organisation-sole-company@2`, 30
`organisation-one-live-company@2`, to 174 bodies. By the body's register:
companies 276, incorporated societies 12, other incorporated bodies 2,
limited partnerships 1, charitable trust boards 1 (also a charity). Near
63 (40 another live, 20 removed before, 3 registered after). Of 550
organisation and estate donation rows, 235 match no body on any of the
four registers: party branches and electorate committees, unions, private
trusts; none is a charity's other name. **No donor organisation newly
confirms to a charity, society or partnership.** So there are no twenty
new confirmed pairs to list. These are the 16 that confirm to a body off
the plain companies register, all already confirmed under @1 through the
Companies Office row:

| Donor as filed | Body | Register | Number | Year |
| --- | --- | --- | --- | --- |
| Auckland Nationalist Centre Inc | AUCKLAND NATIONALIST CENTRE INCORPORATED | incorporated societies | 222194 | 2020 |
| Auckland Nationalist Centre Inc | the same | incorporated societies | 222194 | 2025 |
| The Green Party of Aotearoa New Zealand Incorporated | THE GREEN PARTY OF AOTEAROA NEW ZEALAND INCORPORATED | incorporated societies | 491380 | 2023 |
| Maritime Union of New Zealand | MARITIME UNION OF NEW ZEALAND INCORPORATED | incorporated societies | 509002 | 2017 |
| Maritime Union of New Zealand | the same | incorporated societies | 509002 | 2023 |
| Maritime Union of New Zealand Incorporated | the same | incorporated societies | 509002 | 2020 |
| Maritime Union of New Zealand Inc (two rows) | the same | incorporated societies | 509002 | 2020 |
| Rail and Maritime Transport Union Inc | RAIL AND MARITIME TRANSPORT UNION INCORPORATED | incorporated societies | 643960 | 2020 |
| Toorak Chambers Inc | TOORAK CHAMBERS INCORPORATED | incorporated societies | 214025 | 2017 |
| Toorak Chambers Incorporated | the same | incorporated societies | 214025 | 2026 |
| THE NZ LABOUR PARTY DUNEDIN SOUTH BRANCH INC | THE NEW ZEALAND LABOUR PARTY DUNEDIN SOUTH BRANCH INCORPORATED | incorporated societies | 226912 | 2025 |
| Gilligan Rowe & Associates LP | GILLIGAN ROWE & ASSOCIATES LP | limited partnerships | 2210449 | 2023 |
| Aotearoa Te Kahu Limited Partnership (two rows) | AOTEAROA TE KAHU LIMITED PARTNERSHIP | other incorporated bodies | 50032020 | 2020 |
| MINERALS WEST COAST TRUST | MINERALS WEST COAST TRUST | charitable trust boards (and charities) | 1617222 | 2024 |

**The board and the report, read only, nothing changed.** Groups: the
same pairs confirm to the same refs, so no group moves. Evidence keeps
every @1 key (`company`, `company_number`, `companies_of_that_name`,
`companies_alive_on_date`, `companies_considered`, `live_in_year`, …) and
adds `register`, `registers` and `registers_holding_the_name`; the board
prints evidence whole (`panes.evidence_text`) and the report passes it
through (`walk.link_item`). A future confirmation to a `charities:` or
`societies:` ref opens on both: the board's `links_view.view_for` and the
report's `rows.locate` find the row in the register's views. Rule words are
keyed by name without version (`products/board/catalogue.py`
`rule_words`, `products/report/catalogue.py` `rule_text`), so @2 prints
with @1's words, which say "company". Suggested for the integrator:
"organisation-sole-company": "a donation's organisation name and the one
body of the name on the companies, societies, partnerships and charities
registers, live in its year"; "organisation-one-live-company": the same
with "the one of several bodies". `products/report/check.py:81` and
`products/scan/check.py` read `organisation-name@1` near links, which stay.

## Checks

- Item 4 (rows read every view as it stands) now covers the eight views
  with no change in code: it counts every source in `rows.SOURCES` against
  the catch log, and fails on any difference.
- Item 9, new, in SQL apart from the Python: every @2 link is a donation
  row and a body carrying its name, live in its year by its own register's
  dates; no other body of the name live or undated; sole has one body, one
  live has several; no NZBN names two bodies. Planted in the rolled-back
  sample schema, each turned it red: another body of the name made live; the
  linked company removed before the year (its charity row's dates do not
  keep it live); a society folded apart from its Companies Office twin (both
  items red).
- Items 6 and 7 still check @1 links; none will be built, so they pass on
  none.

## Time and memory

The read-only pass over all 27 views took 48 s; the bodies' SQL 9 s. The
three live `qv4-links-build` runs of 28 October peaked at 958 to 969 MB of
the 4,096 declared, in 18 to 27 minutes. The build holds the components of
the confirmed links in memory (rows +26%, confirmed links about +7%) and
streams the rest; the bodies are copied with no set in memory. Estimate
under 1.4 GB: `memory_gb = 4` in `support/scheduler/jobs.toml` still
covers it (not edited). Read the first run's `peak_mb` to confirm.

## Test pairs and the review agent

The charities officer identifier was expected to supply one-person pairs.
It supplies none: `OfficerId` is the view's key, 589,366 on 589,366 rows.
It keys one officer row, and one person on two charities carries two ids.
Written on the card (still open) and in `measurements.md` section 10. The
switch stays off.

## After the merge

`links.ddl()` runs at the job's start and makes `links.bodies`. No
`links.publish_ddl()`: publish.sql is unchanged. Queue `qv4-links-build`,
then `python -m links.check` live. Nothing here prints a home address or a
suppressed name: the people figures are counts, and the table above is
organisations.

## Result (integrator, 28 October 21:35 NZDT)
Merged 256f4f9 as `integrate/fix-links-3-4` with fix-links-4 (ruling 116), gate green at the first run (the links, board and report slow tests: 18 minutes). At the merge the board's and report's rule words for organisation-sole-company and organisation-one-live-company were reworded for the four registers (rulings 106, 107, 114) and member-on-the-day given its words. publish.sql unchanged, so no DDL by hand; `links.bodies` is made by the job. Released; `qv4-links-build` queued (row 687); the live check runs after it and its peak is read against the 4 GB figure. Branch and working copy retired. Open from this request: the sample database holds none of the published views the lane reads, so a links session cannot do a scratch build (queued for Arthur); the test-pair card stays open.
