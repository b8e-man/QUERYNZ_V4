# The diagnostic subject report: plan (9 November 2026)

Arthur, 9 November 2026: a subject report that touches everything, for internal diagnostic use, to find the
problems before the use-case reports are built. The use-case reports follow, each naming its own significant
information (ruling 146); the banking draft is held at `banking-significance-draft-2026-11-09.md`.

Internal only: local network, like the board. The hard limits on suppressed names and addresses apply as in every
report.

## Where it starts

The subject report (`products/report`) already walks out from one row: the person's group, confirmed links, near
links with their reasons, the companies they sit on, and one step further. Its own template reads 59 of the 131
published tables. The other 72 include insolvency, land titles, sanctions, grants, building practitioners,
councillors' interests, council meetings, court cases, Hansard speakers and party boards. Its "not held" list
still says insolvency, LINZ, sanctions, building practitioners, tenancy, employment and HDC decisions are not held;
all are published now.

## The steps

| # | What | Done when |
| --- | --- | --- |
| 1 | **Inventory.** Every one of the 131 tables sorted: names a person or organisation (the report reads it), or not (a figure, a page, a total), with the reason. The "not held" list corrected | a test fails when a table is published that the inventory does not place, or a register is called not held that is published |
| 2 | **Catalogue entries** for every table that names someone and has none: how its rows are titled, dated and cited. Register by register, a few at a time | every person or organisation table has an entry, and the existing check (every column the catalogue reads exists) passes |
| 3 | **The diagnostic template** (`templates/diagnostic/`): reads every table in the catalogue, walks every reach, depth 2, near links and namesakes listed, every link labelled with its rule | it loads, names only published tables, and builds on a person, a company and an organisation |
| 4 | **"Where else the name appears."** For the subject's name, every register in the name index where the name is filed, against what the walk reached: reached, or held but not reached (counted per register and table, never listed as rows) | a test subject whose name sits in a register no link reaches shows that register under "not reached" |
| 5 | **The test set.** About 20 subjects of every kind, chosen from the registers at run time: see below | each has a report built and saved |
| 6 | **The problems list.** Every problem the 20 reports show, one line each, by kind (below), with the subject and the row | `docs/research/diagnostic-findings-2026-11-09.md` |

Then the problems become the work, and feed the use-case reports' lists.

## The test set

Chosen at run time from the published tables, so the set never goes stale. One or more of each:

1. a sitting MP (Parliament, Hansard, interests, expenses, diaries, donations)
2. a large donor to a party
3. a director of companies that were liquidated
4. a professional director (a hub: fifty or more roles)
5. a very common name (two or more people of the name)
6. a company with a long holding chain
7. a company named in a court judgment
8. a company on a GETS award
9. a charity with officers
10. an incorporated society
11. a council (meetings, councillors' interests)
12. a councillor
13. a person named in the Insolvency Register
14. a building practitioner with a Board decision
15. a body on a sanctions list
16. a grant recipient
17. an iwi or post-settlement entity
18. a person on a ministerial diary
19. a promoter or a party board member
20. a Māori name with a macron

## Tests

Automatic, run with the report's tests:

- every published table is placed by the inventory (step 1); a new table fails the test until placed
- no register in "not held" is published
- every column the catalogue reads exists (exists today)
- the diagnostic template reads every catalogued table
- "where else": a fixed small example where the name sits in two registers and the walk reaches one shows the
  other as not reached
- the presentation rules hold on every report of the test set (exists: no home address, no suppressed name, no
  word of cause, a nominee never shown as owner)
- each report of the test set builds within its time limit (60 s) and its limits are counted, never silent

## Failure modes, and how each is caught

| Failure | How it shows | Caught by |
| --- | --- | --- |
| A namesake shown as the person | a near row under a confirmed heading | the common-name subject; a test that a `name-only` link is never confirmed |
| A near link chained into a confirmed one | a row two near steps out listed as confirmed | the walk's rule (near through near stays near); checked on every report |
| A register held but never reached | the name appears there, no link reaches it | step 4, per subject |
| A register said to be not held when it is | "not held" lists a published register | the step-1 test |
| A table that names people the catalogue does not know | its rows never appear | the step-1 test |
| A column renamed by its lane | the report fails to build | the existing column check |
| The walk explodes on a hub (the Crown, a nominee company, a busy address) | slow report, thousands of rows | limits counted; the 60 s limit; the professional director subject |
| A suppressed name or a home address shown | a breach | the presentation rules, every report |
| A row shown twice by two routes | the same citation twice | a check over each report's citations |
| A date wrong or missing | a connection undated or dated by the wrong column | read by eye on the test set; each undated item counted |
| A citation to a row since removed | a dead reference | the existing check: every citation names a row held today |
| Macrons or name order break matching | the Māori-name subject reaches less than its name appears | step 4 on that subject |
| A link rule joining the wrong things | a confirmed row that is plainly another person or body | read by eye on the test set; recorded with the rule's id |

## Kinds of problem in the findings

wrong link · missing link · register not reached · register not catalogued · wrong date · missing date · slow or
cut short · duplicate · stale "not held" · other
