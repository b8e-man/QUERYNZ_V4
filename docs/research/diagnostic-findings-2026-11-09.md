# The diagnostic subject report: findings (9 November 2026)

One line per problem, by kind (plan: `diagnostic-report-plan-2026-11-09.md`). Fixed ones say by what.

## Found while building it

| # | Kind | Problem | State |
| --- | --- | --- | --- |
| 1 | missing link | Three registers were labelled in the report's catalogue by names of its own (`councils`, `rea`, `building_board`), while the name index and the links call them `councillor_interests`, `real_estate_authority`, `building_practitioners`. A row's reference is `register:key`, so no report ever followed a link from or through those rows: 9,469 links on councillors, 1,508 on Real Estate Authority parties, 324,122 on building practitioners (54,073 confirmed) | fixed: the catalogue uses the registers' own names |
| 2 | stale "not held" | Every report said "not held: Licensed building practitioners"; the register is published (pub.building_practitioners) | fixed: moved to the registers published since |
| 3 | stale "not held" | The list still names insolvency, LINZ titles, sanctions and HDC decisions as not held; all four are published | step 2: with their catalogue entries |
| 4 | register not catalogued | 59 of 131 published tables are in the catalogue; about 35 of the other 72 name a person or organisation (insolvency, land title owners, sanctions, grant recipients, building practitioners, council meetings, Hansard speakers, diary attendees, party boards, iwi entities, …) | step 2 |
| 5 | other | Six tests against the live data fail on the current release too (star namesakes, a prohibition spoke, legal: deed of company arrangement and amalgamation, construction: a shared name never red, healthcare: a liquidated care company): each a template behaving differently on today's data from when it was written | to read one by one |
| 6 | other | Two leftover folders, `registers/charities_a` and `charities_b`, hold only cached files; the OpenLaw lane, dropped on 3 November (ruling 137), still defines pub.court_cases beside the courts lane | noted; harmless |
