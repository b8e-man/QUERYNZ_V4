# The diagnostic subject report: findings (9 November 2026)

One line per problem, by kind (plan: `diagnostic-report-plan-2026-11-09.md`). The test set's 22 reports are in
`/home/user/querynzv4-work/live/diagnostic/2026-11-09/` (a memo carries names, so it stays outside the repository;
`summary.json` holds counts only). Run again with `python -m products.report.diagnose run DIR`.

## Fixed while building it

| # | Kind | Problem | Fix |
| --- | --- | --- | --- |
| 1 | missing link | The catalogue labelled three registers by names of its own (`councils`, `rea`, `building_board`) while the links call them `councillor_interests`, `real_estate_authority`, `building_practitioners`. No report followed any of their 335,099 links (54,073 confirmed) | the registers' own names |
| 2 | stale not held | Every report said insolvency, LINZ titles, sanctions and licensed building practitioners were not held; all four are published | moved to "published since" |
| 3 | register not catalogued | The report read 59 of 131 published tables; 34 more name a person or a body | catalogued; the other 37 listed with why, under a test |
| 4 | wrong date | Councillors' interests and the iwi directory print their dates as text ("16 February 2026", "11/03/2025"): a report that reached one failed to build | text dates in those forms read; anything else shown as printed |
| 5 | other | The land-title sentences said "owner", which the report's own wording check refuses (a shareholder is never called an owner): every report reaching a title refused 396 lines | "registered proprietor", the title's own term |
| 18 | other | Six live-data tests failed on today's data: the star tests' own setup queries timed out on pub.links (millions of land-title links); the legal and healthcare tests expected the courts "not held"; the construction test predated the phoenix check's director path | setup in the walk's query shape; tests read the courts as held in part (amber only on a confirmed party, info on a namesake) |
| 21 | other | The board's live checks: a body's name ("… (Retirement) …") read as a person's home; eight links rules with no words (the judgment-address, judgment-number, shared-contact, land-title and licence-number rules), on the board and in the report; seven people registers with no dossier line, so a near entry read "name · key" (land titles, Real Estate Authority decisions, a minister's diary, insolvency, building practitioners, sanctions, court people) | a row's own kind read; the words and lines written |

## Found by the test set, to decide or fix

| # | Kind | Problem | Seen in |
| --- | --- | --- | --- |
| 6 | wrong link (risk) | **Land title owners are the largest source of name matches.** 5.7 million owner rows; 6.3 million near links on a name alone and 645,057 confirmed on the same full name. They appear in almost every report: 62 rows on a charity's officers, 77 on a director of liquidated companies, 44 on a land owner who is a director | 15 of 22 reports |
| 7 | missing link | **Written questions are not linked to MPs.** A sitting MP's name is on 51 written questions no link reaches | the MP |
| 8 | missing link | **Mentions in Beehive releases, Hansard and Parliament's pages do not reach diary attendees or Board decision parties.** The name is filed there (17 Beehive mentions for one diary attendee) and no link joins it | the diary attendee; the Board decision party |
| 9 | missing link | **The building practitioners' licence register and the Board's decisions never join.** The published decisions carry no licence number, so a decision is matched to nobody; the one Board-decision party in the test set reached nothing at all | the Board decision party |
| 10 | missing link | **A GETS supplier's name is in 12 court rows and 1 Board decision that no link reaches** | the supplier |
| 11 | wrong date | **149 of 150 annulled bankruptcies carry no annulment date** in pub.insolvency_people, so the report says "no end filed" for a bankruptcy that was annulled | the insolvency subject |
| 12 | other | **No director's name in the companies register carries a macron** (0 of all directors), while the name index holds 92,370 names with macrons from other registers. Either the Companies Office file or our copy strips them; a Māori name then matches across registers only by its folded form | the Māori-name case |
| 13 | other | **The Gazette and the Insolvency Register treat an annulment differently.** The Gazette lane withholds a name on every earlier row once an annulment names it; the Insolvency Register lists annulled cases by name | the insolvency subject |
| 14 | slow or cut short | **The walk is cut short on a very common name**: 292 links, 258 entities and 370 group rows left out (all counted, as designed). A professional director: 22 entities omitted | the common name; the professional director |
| 15 | missing date | **Shareholdings and land titles are undated** (the registers state no date): up to 121 undated items in one report. Stated as undated, with why | most reports |
| 16 | other | **A table carries one kind for all its rows**, though sanctions, land title owners, Hansard, Beehive and Parliament mentions and diary attendees mix people and bodies; a body in such a table is walked as a person | the catalogue |
| 17 | other | **The name index calls a marae a person**, and a marae's row reference carries its street location | the iwi directory |
| 18 | other | (fixed, above) Six live-data tests fail on the current release too (star namesakes, a prohibition spoke, legal: deed of company arrangement and amalgamation, construction: a shared name never red, healthcare: a liquidated care company); each a template behaving differently on today's data from when it was written | the template tests |
| 19 | other | Two leftover folders (`registers/charities_a`, `charities_b`) hold only cached files; the OpenLaw lane, dropped on 3 November (ruling 137), still defines pub.court_cases beside the courts lane | the repository |
| 20 | stale not held | **Eleven use-case templates still say the Insolvency Register is "interface awaited" and court judgments are "step 5.4"**, and the legal template that real estate agents' and builders' findings are not held; all are published. Which of them each template reads is ruling 146's choice, product by product | the use-case templates |

## Working as designed (checked, no change)

- A trustee company's director with 670 rows in one group: the group is flagged contested, every other row is near.
- "Same full name" confirms only with a middle name (all 1,132,177 confirmed full-name links among directors have one).
- Every report built in under 23 s; the slowest was a company with a holding chain.

## What this means for the use-case reports (ruling 146)

Findings 6 and 8 are the case for choosing significant information product by product: a report that reads land
titles and the Hansard, Beehive and Parliament mentions draws in name matches on almost every subject. Each
use-case report should name whether it reads them at all, and if so by which links.

## Worked on 9 November, evening

| # | Outcome |
| --- | --- |
| 7 | **Fixed.** Written questions were linked (582,019 confirmed) but the report could not open a ref carrying the person's part (`#asker`, `#minister`) and dropped every one; the sitting MP's report now lists all 51 |
| 8 | **Not a gap.** Both subjects were filed under a surname alone (564 of 787 Board decision parties, 28,183 diary attendees), which every register files and no rule should join on; the diagnostic now looks for no surname alone and starts these cases from a full name, and with one every row is reached |
| 9 | **Corrected, rule proposed.** The decisions do print the licence number (787 of 794, `BP123456`); 496 are on today's register. Proposed `lbp-number@1`, as the Real Estate Authority's licence rule: confirmed where the names agree (132 by first and last name, 351 by the surname a decision prints alone), near otherwise (13). 20 pairs for Arthur: `/home/user/querynzv4-work/live/diagnostic/2026-11-09/pairs-board-decisions.md` |
| 10 | **Not a gap**, as 8: the supplier's name is one word, read as a person; the 12 court rows are the same word |
| 11 | **Fixed.** A search answer gives no annulment date and details were asked in estate order; ended estates are now asked first (157, inside one night's run), and the report says "annulled", never "no end filed" |
| 12 | **The source's.** No raw Companies Office answer carries a non-ASCII character in a person's name (the API's lookups too: 0 of 31,624 roles); our copy strips nothing. The fold already matches the folded form |
| 16 | **Fixed.** Ten tables that say each row's kind are read by it (`catalogue.ROW_KIND`): a body there is walked as a body |
| 17 | **Fixed** (at the next links build): every iwi directory row is a body (2,545 of 2,697 were read as people). A marae's key carries its place, a public place, not a home: no change |
| 19 | The OpenLaw file is never run (ruling 137 keeps it as the record); `pub.court_cases` is the courts lane's. The two `charities_a`/`charities_b` folders hold 17 compiled files; the safety hook refuses a recursive delete, so Arthur removes them |
| — | A construction report was refused: a fired flag quoting a society's registered name ("… PEST CONTROL …") read as a word of cause. Flags are now judged on the report's own words, as items are |
