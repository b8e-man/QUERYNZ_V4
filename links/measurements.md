# The six first measurements (plan 4.2), 20 October 2026 (links-2, second run)

Run on the real published tables through `python -m links.measure` in
`scratch_links_2`; the figures are in `links.measurements` (JSON) and
summarised here. Nothing here comes from the sample. Bands: a first-and-last
name carried by 1 to 5 director rows is rare, 6 to 50 middling, over 50
common. The first run (links-1, the same morning) is in git; what moved
between the two is said under each heading. Two things moved every figure:
the rows now read every published register (nineteen views, 2.88 M rows),
and the given name is the first given name whichever field a lane filed it
in (26,294 director rows whose first-name field held two names now carry a
middle name).

## 1. How often a full name repeats

| Band | First-and-last names | Director rows | Rows with a middle name | Names on one row only |
| --- | --- | --- | --- | --- |
| rare | 519,980 | 787,045 | 551,353 | 357,688 |
| middling | 27,509 | 316,676 | 243,495 | 0 |
| common | 879 | 81,865 | 68,922 | 0 |

Full names with a middle name: 487,317 names on 863,779 rows; 135,080
names repeat (511,542 rows); the most repeated carries 662 rows. Without a
middle name: 193,777 names on 321,870 rows; 49,529 repeat (177,622 rows);
the most, 648. Of the other registers' rows, the share whose first and last
name is also on the director register: shareholders 86%, society officers
44%, Gazette bankrupts 31%, liquidators 67%, MPs' expense lines 47%,
ministers' expense lines 54%, Gazette appointees 42%, MPs' returns 49%,
candidates 44%, donors (Part A) 51%, filing candidates 43%, disclosures 71%,
promoter people 46%, members 47%.

## 2. Addresses shared by many companies

Unchanged from the first run: 1,188 busy addresses (over 50 companies)
hold 191,216 companies, 22% of all; the busiest holds 2,463.

| Companies at the registered office | Addresses | Companies |
| --- | --- | --- |
| 1 | 351,139 | 351,139 |
| 2 to 5 | 89,549 | 222,316 |
| 6 to 50 | 8,161 | 101,969 |
| 51 to 200 | 912 | 88,528 |
| over 200 | 276 | 102,688 |

## 3. The error rate of the two confirming rules

On the test pairs (`links.pairs`, seed 43, redrawn on the new rows: the
pool of two-directors pairs is 754, not 430, because the given-name fix
keys more rows together). Error on a "two people" pair means the rules
confirmed it; on a "one person" pair, that they did not.

| Kind | Truth | Band | Pairs | Confirmed by rule 1 | By rule 2 | Error rate | Of which identical full name with middle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| two directors, one name, one company at once | two people | rare | 200 | 37 | 40 | 38.5% | 37 |
| | | middling | 200 | 14 | 30 | 22.0% | 14 |
| | | common | 31 | 6 | 5 | 35.5% | 6 |
| two candidates, one name, different electorates | two people | middling | 1 | 0 | 0 | 0% | 0 |
| a seat and its winning candidacy | one person | rare | 137 | 0 | 0 | 0% as built (the lane's own identifier; the name rules never confirm a politician) | 14 |
| | | middling | 7 | 0 | 0 | 0% as built | 0 |
| a candidate across an original and an amended return | one person | rare | 2 | 0 | 0 | 0% as built (`source-identifier@1`, new: the Commission's `replaced_by`) | 1 |

The two caveats of the first run stand: rule 2 confirms two roles on one
company by that company's own office (queued:
`does-one-company-s-office-count-as-a-shared-address`), and a pair with an
identical full name and middle name on one company may be the register
listing one person twice. Without those pairs: rare 20.0%, middling 15.0%,
common 16.1%, all by rule 2 on the shared company. The first run's rare
figure (52.0%) was on a different draw and is not comparable.

The review agent's reading of 100 confirmed links (first run, seed 7): 98
"no reason to doubt", 2 "contested"; an agent's judgment, not re-run here.
Track C's scoring is below.

## 4. How often each rule can fire, per register

| Register, view | Rows | Rule 1 can compare a middle name | Rule 2 has a company address | Politician (never confirmed by name) |
| --- | --- | --- | --- | --- |
| companies, shareholders (individuals) | 1,376,457 | 987,353 | 1,376,062 | 0 |
| companies, directors | 1,185,649 | 863,779 | 1,185,646 | 0 |
| societies, officers | 133,003 | 48,376 | 0 | 0 |
| gazette, bankruptcies (new) | 64,741 | 52,939 | 0 | 0 |
| gazette, liquidators | 45,065 | 26,787 | 0 | 0 |
| expenses, MPs' lines (new) | 26,689 | 1,090 | 0 | 26,689 |
| expenses, ministers' lines (new) | 13,467 | 575 | 0 | 13,467 |
| gazette, appointments (new) | 3,145 | 1,553 | 0 | 0 |
| mp_interests, returns | 2,526 | 129 | 0 | 2,526 |
| house, candidates | 1,615 | 221 | 0 | 1,615 |
| party_returns, donors (people) | 876 | 183 | 0 | 0 |
| mp_interests, declared interests in a person's name (new) | 615 | 213 | 0 | 615 |
| gazette, prohibitions | 536 | 440 | 0 | 0 |
| candidate_returns, filing candidates | 385 | 36 | 0 | 385 |
| disclosures (people) | 359 | 108 | 0 | 0 |
| party_finance, promoter people | 303 | 26 | 0 | 0 |
| house, members | 243 | 27 | 0 | 243 |
| candidate_returns, donors (people) | 118 | 21 | 0 | 0 |
| disclosures, items | 26 | 26 | 0 | 0 |

Links made, 2,815,624 (first run 2,613,986): rule 1 1,289,139 (companies
to companies 1,237,378; to Gazette 18,274; to societies 16,013; Gazette to
Gazette 15,095, bankrupts among them); rule 2 961,132 (all within
companies); the number 4,392 (8 of them a company number a member printed
in a declaration); the lane's own join 146 (seats to candidacies 144, a
candidate across an amended return 2); name-only near 444,611.

The rules of this run, each from a register's own structure or a named
circumstance (`links/build.py`):

| Rule | Grade | Links | What joins |
| --- | --- | --- | --- |
| `seat-and-window@1` | confirmed | 23,042 | a House row (685 interests returns, 22,357 expense lines) to the seat whose term covers it, same name, electorate agreeing; 0 near (two members of one name in a window) |
| `declared-directorship@1` | confirmed | 434 | a member's return to a director row of the member's name on a company the member declared (86 returns) |
| `organisation-name@1` | near | 3,228 | a declared company (2,917) or an organisation donor (311) to the companies of that name |
| `company-name@1` | near | 88,819 | companies under one name (75,184) or one name apart from a bracketed year (13,635) |
| `candidate-name-form@1` | near | 402 | one name for one party across elections (37 under two printings) |
| `filed-name@1` | near | 172 | donation rows under one organisation name |
| `member-and-party-donor@1` | near | 106 | a member's name on a donor row to the member's party in the term |
| `own-return@1` | near | 1 | a donor row in the candidate's own name on the candidate's return |

House rows that found no seat: 19,196 dated before the first seat row the
house lane holds (ge-2020), and 1,091 in the seats' window, nearly all a
member who entered on a list vacancy and is no seat row (card
`who-left-the-house-mid-term-is-not-in-the-results-files`) or a name the
House prints two ways ("LEAVASA, Neru" and "Leavasa, Anae Neru").

## 5. Company names to official numbers

| Register | Organisation rows | Exactly one company alive on the date | Several | Name held, none alive | No company of that name |
| --- | --- | --- | --- | --- | --- |
| disclosures | 150 | 94 (63%) | 0 | 1 | 55 |
| party returns (Part A) | 247 | 152 (62%) | 0 | 3 | 92 |
| candidate returns (new) | 57 | 9 (16%) | 0 | 16 | 32 |
| MPs' declared interests (new; the return's date) | 3,593 | 2,303 (64%) | 41 | 185 | 1,064 |

## 6. The shape of the groups

681,618 groups over 2,315,026 rows (first run 669,863 over 2,251,437);
52,085 contested by the watch (152,771 of 2,250,271 confirmed links
flagged: 143,922 regions apart, 8,714 a very common name without a middle
name, 149 a bankruptcy with a directorship taken up within three years of
it, a new flag); no group contradicts a `not the same` decision (5,472
decisions promoted from the old ledgers). 172 groups hold a seat; 40 of
them reach the companies register through a declared directorship, 129
hold a seat with its returns and expense lines.

| Rows in the group | Groups | Rows | Contested | Spanning registers |
| --- | --- | --- | --- | --- |
| 2 | 445,171 | 890,342 | 6,397 | 7,130 |
| 3 to 5 | 167,515 | 623,726 | 23,580 | 12,376 |
| 6 to 20 | 64,040 | 540,430 | 19,514 | 4,687 |
| 21 to 100 | 4,383 | 165,831 | 2,366 | 819 |
| over 100 | 509 | 94,697 | 228 | 203 |

The largest, 1,220 rows across companies, Gazette and societies, is a
professional trustee director; the next two are liquidators named on
hundreds of notices. (The first run's page said 669,863 groups "over
2,251,437 rows" from the build log; measurement 6 itself counted groups
twice, fixed in this run.)

## 7. Ruling 106's three rules, 28 October 2026 (links-3)

`scratch_links_3` on the real published tables: the rows gathered once, built
with the code before the rules (before) and with them (after) over the same
rows; the live decisions copied in. Groups 681,628 → 681,815, rows in groups
2,315,125 → 2,315,735, contested 52,085 → 52,085, largest 1,220 → 1,220.

- `organisation-sole-company@1`: 315 donation rows (party returns, candidate
  returns, declarations) have a company of their name. 262 confirmed (one
  company of the name, live in the year); near: 70 pairs (30 rows) several
  companies (every one of the 30 has exactly one live: queue item
  `one-company-of-several-live-in-the-donation-s-year`), 20 removed before
  the year, 3 registered after it. The 2,195 declared-interest pairs
  (`mp_interests`) are not donations and stay as they were. 418 rows (262
  donations, 156 companies) now sit in 156 groups; 178 of them were in 87
  groups before; none contested.
- `successor-name@1` (related, "succeeded by"): judged on every pair the name
  pattern makes, 17,366 (the near star stores 13,635); 951 share a person
  confirmed on both (2,935 shared people, 639 with more than one), 3
  ordered by key because the registration dates are equal. The 928 star
  pairs among them leave `company-name@1`, 12,707 stay near. In 86 the
  company carrying the year was registered first (renamed when the new one
  took the plain name). No group holds both companies of any (check 6).
- `candidate-same-party@1`: 206 names under one party in more than one
  election, 282 confirmed pairs, none refused (no name stands twice for a
  party in one election today). `candidate-name-form@1` 402 → 180 (143 same
  printing, members' seats; 37 different printings). 488 candidate rows in
  206 groups; 118 were in 88 groups before (each seat to its candidacy);
  3 contested before and after.
- Test pairs redrawn: `two-candidates-one-election` 0 of 1 in one group (two people, as it should);
  `member-and-candidacy` 144 of 144 (one person, as it should).

## 8. Ruling 107's rule, 28 October 2026 (fix-links-1)

`scratch_fix_links_1` on the real published tables, as in 7: the rows
gathered once (2.86 M rows from nineteen views, 5,694 live decisions copied
in), built with main's code (before, which equals links-3's after: 681,815
groups) and with this rule (after) over the same rows. Groups 681,815 →
681,832, rows in groups 2,315,735 → 2,315,782, contested 52,085 → 52,085,
largest 1,220 → 1,220.

- `organisation-one-live-company@1`: 30 donation rows have a name several
  companies carry; in all 30 exactly one was live in the year (none with
  no live company, none with two). **30 confirmed**, to 18 companies; the
  other 40 pairs of those rows stay near under `organisation-name@1`, "this
  one was not live in the donation's year, and the one that was is
  confirmed". `organisation-name@1`'s "several companies" pairs 792 → 722
  (all `mp_interests`, unchanged). The 48 rows (30 donations, 18
  companies): 1 in a group before, 48 in 18 groups after; none contested.
  Christopher & Banks Limited is two companies: 3482091 (removed
  2024-12-18) takes the 2022 and 2023 gifts, 9321019 (registered
  2025-03-06) the 2025 and 2026 ones.
- Test pairs: a new kind, `donor-and-company-not-live` (a donation row and
  a company of its name the register shows was not live in the year): 63
  drawn (40 from this rule's names, 23 from ruling 106's one company), 63
  measured, 0 confirmed by the rules, 0 in one group. The company is not a
  row of `links.rows`, so measurement 3 judges these with
  `rules.sole_company`; the review agent does not score them.
- Check 7 (`check.py`): 292 confirmed donation-to-company links, 0 to a
  company not live in the year, 0 where two were live. Planted in a rolled-
  back transaction, each turned it red: the linked company registered after
  the year (1), a second company of the name made live (4), a ruling 106
  link relabelled as this rule's (1).

## 9. Ruling 109's rule, 28 October 2026 (fix-links-2)

`scratch_fix_links_2` in querynz_v4: `links.org_names`, `rows`, `groups`
and `decisions` copied from the live tables with the `company-name@1` and
`successor-name@1` links; `refiled-name@1` built over them with the people's
components read from the live groups (the groups do not change: a related
link is never walked). 15 s for measurement 9.

- Companies under one name key with no year in brackets, one of the two
  removed: 85,763 pairs. **12,607** have the other registered within twelve
  months of the removal, before or after it. 7 of those have a director or
  shareholder row on both companies, 5,559 on one only; **2 share a
  confirmed person, and 2 relate**: CHATHAM ROCK PHOSPHATE LIMITED 1819800
  (registered 2006-06-07, removed 2026-07-31) → 9446991 (registered
  2026-07-31, same day), 4 people on both; PACIFIC HYGIENE LIMITED 564741
  (registered 1992-11-10, removed 2026-07-31) → 9444168 (registered
  2026-07-13, 18 days before the removal), 3 people on both.
  `company-name@1` near 87,891 → 87,889.
- Why so few: the published register keeps people for 759,286 of 820,830
  registered companies and for 3,360 of 1,099,638 removed ones. A removed
  company keeps its people only where a monthly file the companies lane
  holds still listed it (both related pairs were removed on 2026-07-31).
  Christopher & Banks Limited 3482091 (removed 2024-12-18) has no director
  or shareholder row in `pub.directors` or `pub.shareholders`, and
  `pub.company_lookup_roles` is empty, so no person can be confirmed on
  both; it stays near (`company-name@1`). Queued:
  `a-refiled-company-whose-removed-half-has-no-people`.
- Test pairs: two new kinds, `companies-refiled-within-twelve-months` (7
  drawn, every pair the registers supply) and
  `companies-one-name-beyond-twelve-months` (2), both "two people" (two
  bodies). Measurement 3: 0 in one group; 2 related, 0 related beyond the
  twelve months, 0 related with no shared person.
- Checks (`check.py`): item 6 now reads both relations (953 related, 0 in
  one group, 0 of another rule or relation, 0 without a person in one group
  on both); item 8, new, 2 refiled relations, 0 outside the twelve months,
  0 names that do not fit, 0 with no shared person. Planted in a rolled-
  back transaction, each turned items 6 and 8 red: a refiled relation five
  years apart (1), one with no shared person (1).

## 10. Ruling 114's views and registers, 28 October 2026 (fix-links-1, second fix)

A session may no longer write the live database (`support.db` refuses the
owner login there), and the sample database publishes no views the rows can
read, so this is a read-only run of the new code over the live published
views through the read login, nothing written: the eight views through
`rows.row_record` as the gather reads them, the bodies through
`rows.BODY_SQL`, the donation rows through `rules.sole_body`, the near and
full-name links estimated against the live groups (a row joins the group of
any row of its full name with a middle name, as rule 1 makes them).
Measurement 10 in `measure.py` counts the same from the tables after the
first live build.

**People.** The rows grow 2,861,853 → 3,619,802 (+757,949) and the name
keys 1,010,393 → 1,339,246 (+328,853). No existing view loses a row to the
new set-aside (a bare initial, or a name that is nothing outside brackets).

| View | Read | Written | Set aside | Name keys | Near pairs added | Full-name links added |
| --- | --- | --- | --- | --- | --- | --- |
| charity officers (people; 3,271 body corporate not read) | 586,095 | 586,095 | 0 | 424,218 | 259,520 | 124,072 |
| Gazette celebrants | 159,502 | 159,502 | 0 | 37,678 | 104,634 | 35,787 |
| Gazette receivers and administrators | 6,045 | 6,045 | 0 | 687 | 2,261 | 3,681 |
| party board roles | 2,876 | 2,876 | 0 | 116 | 2,850 | 8 |
| local election candidates (204 rows for several candidates name nobody) | 1,979 | 1,976 | 3 "(combined)" | 1,560 | 1,134 | 0 (politician) |
| building practitioner decisions | 264 | 261 | 3 suppressed | 224 | 173 | 14 |
| limited partnership partners (people; 3,573 bodies not read) | 139 | 139 | 0 | 126 | 38 | 49 |
| councillor interests | 56 | 56 | 0 | 15 | 51 | 0 (politician) |
| **all eight** | | **757,949** | | | **373,477** | **166,841** |

Each view's figures are with that view alone added. Party board roles are
one row per captured page, so 116 names make 2,850 near pairs. Local
candidates and councillors are politicians to the rules (near by name,
never confirmed), as MPs and candidates are.

**Organisations.** `links.bodies`: 1,920,468 Companies Office rows (every
register `pub.companies` holds), 53,271 societies and 3,380 limited
partnerships (every one the same body as a Companies Office row by NZBN,
with the same number and dates), 46,139 charities (31,532 the same body as
a Companies Office row: 29,384 by the NZBN the charities register carries,
the rest by the company, society or trust-board number it carries where its
legal structure names that register; 14,607 charities alone). Donation rows
with a body of their name: 315, as before. **292 confirmed, the same 292
pairs as @1** (262 `organisation-sole-company@2`, 30
`organisation-one-live-company@2`); 0 new, 0 lost. By the body's register:
companies 276, incorporated societies 12, other incorporated bodies 2 (a
limited partnership the published partnerships register does not carry),
limited partnerships 1, charitable trust boards 1 (also a registered
charity). Near 63 (40 another was live, 20 removed before the year, 3
registered after it); 6 now name "the companies and incorporated societies
registers". Of the 550 organisation and estate donation rows, 235 have no body of
their name on any of the four: party branches and electorate committees,
unions, private trusts; none is a charity's other name. Why no charity is
new: the societies, partnerships and trust boards the rule needed were
already rows of `pub.companies`, and no donor's name is a charity's alone.

**Time and memory.** The read-only pass over all 27 views took 48 s; the
bodies' SQL 9 s. The three live `qv4-links-build` runs of 28 October peaked
at 958 to 969 MB of the 4,096 declared, in 18 to 27 minutes. The build
holds in memory the components of the confirmed links (rows +26%,
confirmed links about +7%) and streams the rest; the bodies are copied
without a set in memory. Estimate: under 1.4 GB, within the declared 4 GB.

**Test pairs.** The charities officer identifier keys one officer row:
589,366 identifiers on 589,366 rows, none repeated. One person on two
charities, or across two returns, carries two identifiers, so it supplies
no one-person pair (card `three-test-pair-kinds-the-registers-cannot-supply`).
The review agent's switch stays off.

## 11. Ruling 116's rule, the member on the day, 28 October 2026 (fix-links-1, fourth fix)

Measured before the build, read-only on live through the read login,
through the code of this fix (`rows.SOURCES`, `rows.row_record`,
`rules.member_on_the_day`) against `pub.members` as it stands (243 rows:
the 2020 and 2023 general elections and the 2025 Tāmaki Makaurau
by-election, so the first day it holds is 17 October 2020). Nothing was
written. Measurement 11 (`measure.m11_ruling_116`) counts the same from
the tables after the build.

**The match is by first and last name** (`fl_key`), the titles off
(`rows.MEMBER_TITLES`): the House files middle names the other views do
not print ("SEYMOUR, David Breen", "Seymour, Hon David"), so the full name
key would miss them; middle names that differ on both rows take the
member out. A member sits from `from_on` up to, not on, `to_by` (no row
carries `ended_on`): the polling day begins the new term, so a re-elected
member's two terms never both cover a day.

| Rows of | Rows | One member sitting (confirmed) | Two or more | A member of the name, another time (near) | No member of the name | Before 17 Oct 2020 |
| --- | --- | --- | --- | --- | --- | --- |
| hansard_speeches (a turn with a name; 7,145 Speaker turns print none) | 40,098 | 37,874 | 0 | 958 | 1,266 | 0 |
| parliament_written_questions, the asker (8,678 withdrawn questions name none) | 674,846 | 267,757 | 0 | 19,877 | 32,051 | 355,161 |
| parliament_written_questions, the minister | 674,846 | 314,262 | 0 | 0 | 5,423 | 355,161 |
| beehive_release_ministers | 5,742 | 5,742 | 0 | 0 | 0 | 0 |
| minister_diary_releases (dated by the month's last day) | 2,560 | 1,911 | 0 | 0 | 30 | 619 |

No row finds two members. A day before 17 October 2020 makes no link:
the members view holds no term then, so it could not have seen the
member (the 2003 to 2020 questions, the 2017 to 2020 diaries).

**The names that most often find none** on a day the view holds (every
one there is; fewer than twenty a view): askers Francisco Hernandez
29,013, Camilla Belich 13,974, Dr Tracey McLellan 2,135, Dr Lawrence
Xu-Nan 1,731, Shanan Halbert 1,498, Vanushi Walters 1,051, Sam Uffindell
566, Glen Bennett 445, Mike Davidson 303, Harete Hipango 235, Benjamin
Doyle 231, Celia Wade-Brown 216, Dan Rosewarne 213, Tama Potaka 208,
Georgie Dansey 109; speakers the same people and Laura McClure 142, Nancy
Lu 128, Dr David Wilson 72; ministers and diaries "Hon Kiritapu Allan"
(5,423 and 30). Belich, McLellan, Halbert, Walters and Bennett are in
the view for the 2020 term only, Uffindell and Potaka for 2023 only
(each came in at a 2022 by-election the view lacks); the rest are not in
it at all. These are the card's members (list members who filled a
vacancy, by-election winners the view lacks), the expected abstentions.
No honorific form is left: no key of the 1,398,092 rows carries a title
word. One name form: the House files "ALLAN, Kiri"; "Kiritapu" is not
"Kiri" under the one reading of names, and is never guessed.

**Parliament's member id**, carried in the evidence: 133 ids on the
confirmed turns and askers, none naming two members, no member under two
ids. The name-and-day rule and Parliament's own id agree on every row
where both exist.

**Ten confirmed pairs a view** (as printed → the member row):

| View | Pairs |
| --- | --- |
| hansard_speeches | Leary, Ingrid → LEARY, Ingrid (ge-2023 Taieri, 21 Nov 2024); Peters, Rt Hon Winston → PETERS, Winston (ge-2023 list); Anderson, Miles → ANDERSON, Miles (Waitaki); Bayly, Hon Andrew → BAYLY, Andrew (list); Luxon, Rt Hon Christopher → LUXON, Christopher (Botany); Carter, Kahurangi → CARTER, Kahurangi (list); Jones, Hon Shane → JONES, Shane Geoffrey (list); Seymour, Hon David → SEYMOUR, David Breen (Epsom); Kuriger, Barbara → KURIGER, Barbara (Taranaki-King Country); Hipkins, Rt Hon Chris → HIPKINS, Chris (Remutaka) |
| written questions, asker | Debbie Ngarewa-Packer → NGAREWA-PACKER, Debbie (Te Tai Hauāuru); Tangi Utikere → UTIKERE, Tangi (Palmerston North); Ricardo Menéndez March → MENENDEZ MARCH, Ricardo (list); Teanau Tuiono → TUIONO, Teanau (list); Hon Dr Ayesha Verrall → VERRALL, Ayesha (list); Hon Willow-Jean Prime → PRIME, Willow-Jean (list); Chlöe Swarbrick → SWARBRICK, Chlöe (Auckland Central); Rawiri Waititi → WAITITI, Rawiri (Waiariki); Simeon Brown → BROWN, Simeon (ge-2020 Pakuranga); Dr Shane Reti → RETI, Shane (ge-2020 list) |
| written questions, minister | Rt Hon Winston Peters → PETERS, Winston (list); Hon Tama Potaka → POTAKA, Tama William (Hamilton West); Hon Simeon Brown → BROWN, Simeon (Pakuranga); Hon David Seymour → SEYMOUR, David Breen (Epsom); Hon Mark Patterson → PATTERSON, Mark (list); Hon Chris Bishop → BISHOP, Chris (Hutt South); Hon Simon Watts → WATTS, Simon (North Shore); Hon Mark Mitchell → MITCHELL, Mark (Whangaparāoa); Hon Judith Collins → COLLINS, Judith (Papakura); Hon Michael Wood → WOOD, Michael Philip (ge-2020 Mt Roskill) |
| beehive_release_ministers | Rt Hon Christopher Luxon → LUXON, Christopher (Botany); Hon Mark Patterson → PATTERSON, Mark (list); Hon Todd McClay → McCLAY, Todd (Rotorua); Hon Andrew Hoggard → HOGGARD, Andrew John (list); Hon Shane Jones → JONES, Shane Geoffrey (list); Hon Casey Costello → COSTELLO, Casey (list); Hon Brooke van Velden → VAN VELDEN, Brooke (Tāmaki); Hon Judith Collins KC → COLLINS, Judith (Papakura); Hon Erica Stanford → STANFORD, Erica (East Coast Bays); Hon Tama Potaka → POTAKA, Tama William (Hamilton West) |
| minister_diary_releases | Hon Chris Bishop → BISHOP, Chris (Hutt South, June 2026); Hon Karen Chhour → CHHOUR, Karen (list); Hon Chris Penk → PENK, Chris (Kaipara ki Mahurangi); Hon Dr Shane Reti → RETI, Shane (Whangārei); Hon Andrew Little → LITTLE, Andrew (ge-2020 list, January 2021); Hon Paul Goldsmith → GOLDSMITH, Paul (list); Hon Nicole McKee → McKEE, Nicole (list); Hon Louise Upston → UPSTON, Louise (Taupō); Hon Dr Megan Woods → WOODS, Megan (ge-2020 Wigram); Hon Kelvin Davis → DAVIS, Kelvin (ge-2020 Te Tai Tokerau) |

**Volume, time and memory.** Rows 3,618,803 → 5,016,895 (+1,398,092,
+39%; the written questions 1,349,692 of them). Reading every source
read-only through server cursors: 48 s for the 27 views, 69 s for the 31.
The rule over the new rows, read-only: 28 s, 277 MB peak for the whole
process. Links to come: 627,546 confirmed and 20,835 near, one a row (no
star); the rows take no `name-only@1` star, so the near step does not
grow. The build holds the confirmed components in memory: about 628,000
more rows there (about +150 MB). From the three runs of 28 October
(958 to 969 MB of 4,096): about 1.2 GB, so `memory_gb = 4` still covers
it; time about three minutes more on 18 to 27. The sample database holds
none of these views (six questions and three release ministers in a
scratch schema), so these figures are live and read-only, as section 10's
were; read the first run's `peak_mb`.

## 12. Ruling 125's rule, the organisation rules on every row, judged on the row's date, 30 October 2026 (links-5)

Measured before the build, read-only on live through the read login,
through the code of this session (`rules.body_on_date` over every
organisation-named row of `links.rows`, 5,642 rows in fourteen views,
against `links.bodies` as it stands: 3,339 rows have a body of their name,
1,178 bodies), 1 s, nothing written. Measurement 12
(`measure.m12_ruling_125`) counts the same from the tables after the build.

**The date is the row's own**, `started_on` .. `ended_on` as the view files
it: a donation's return year or its given day, an interests return's date,
an officer's appointment, a director's appointment, a Gazette notice's
date; a body registered on or before the window's end and not removed
before its start was live. `pub.shareholders` publishes no filing date, so
every holder row is undated and stays near (card
`pub-shareholders-publishes-no-filing-date-so-every-organisation-named-holding-stays-undated`).

| View | Rows | Dated | With a body of the name | One body of the name: live on the date (confirmed, sole) / registered after / removed before | Several bodies: one live on the date (confirmed) / more than one / none | Undated rows (near, "undated") |
| --- | --- | --- | --- | --- | --- | --- |
| mp_interests | 3,593 | 3,593 | 2,529 | 2,190: **2,039** / 64 / 87 | 339: **259** / 46 / 34 | 0 |
| shareholders | 1,170 | 0 | 446 | 0 | 0 | 446 (484 near links) |
| party_return_donors | 291 | 291 | 185 | 167: **163** / 3 / 1 | 18: **18** / 0 / 0 | 0 |
| directors | 154 | 154 | 3 | 3: **2** / 0 / 1 | 0 | 0 |
| disclosures | 151 | 151 | 96 | 84: **83** / 0 / 1 | 12: **12** / 0 / 0 | 0 |
| candidate_return_donors | 87 | 87 | 34 | 34: **16** / 0 / 18 | 0 | 0 |
| society_officers | 77 | 77 | 26 | 24: **24** / 0 / 0 | 2: **1** / 1 / 0 | 0 |
| charity_officers | 77 | 75 | 19 | 17: **15** / 1 / 1 | 0 | 2 |
| gazette_appointments | 10 | 1 | 1 | 0 | 0 | 1 (several bodies) |
| gazette_celebrants 21, gazette_bankruptcies 6, gazette_liquidators 2, local_election_returns 2, gazette_practitioners 1 | 32 | 32 | 0 | | | |

**Confirmed: 2,632 rows, one link each** (2,342 `organisation-sole-company@3`,
290 `organisation-one-live-company@3`), where @2 confirmed 292 (the donor
and disclosure rows, unchanged: party donors 181 of 291, candidate donors
16 of 87, disclosures 95 of 151, the same pairs). By the body's register:
companies 2,577, incorporated societies 28, limited partnerships 20,
charitable trust boards 5, other incorporated bodies 2. Near: 1,182 links
under `organisation-name@1` (mp_interests 624: another was live 307,
removed before 87, registered after 64, none live 72, more than one 94;
shareholders 484 undated; the donors' 63 as before; directors 1, society
officers 4, charity officers 4, gazette_appointments 2). The declared
interests' old near step (every company of the name on the companies
register, 2,917 links) is replaced: the same rows now take 2,922 links,
2,298 of them confirmed.

**Against the queue item's figures** (MPs' interests 2,139 rows with
exactly one body and 239 with one live body of several; shareholders 76
and 5; society officers 16; charity officers 18; directors 2). Those were
counted with "live" as today. Counted the same way here (a body with no
removal date and no undated removal), the rows with exactly one body of
the name are 2,190 for the interests, 410 for the holders, 24 for society
officers, 19 for charity officers and 3 for directors, of which live today
1,557, 395, 20, 16 and 2, and the several-with-one-live-today 232, 3, 1, 0
and 0; the item's method is not written down and is not reproduced
exactly. The time-aware figures above are the rule's. The direction is the
ruling's: on the row's date the interests confirm 2,298 rows (2,039 +
259), more than today's count, because a return of 2006 to 2017 names
companies since removed, which were live when declared (87 rows whose one
body was removed before the return and 64 registered after it stay near,
with the reason).

**The case the brief names, on live: 33 rows** where the one body of the
name live today was not the one alive on the row's date, and the rule
confirms the one that was: the disclosures of Christopher & Banks Ltd
(12 May 2022, 13 March 2023, 13 June 2023) to company 3482091 (registered
2011, removed 18 December 2024), not 9321019 (registered 6 March 2025),
ruling 109's own pair; and in the interests returns Ivory Limited (2016,
2017: 3751657, removed 2017, not 8263494 of 2021), Bakshi Enterprises
Limited (2012 to 2017: 1135334, removed 2017, not 9297701 of 2024), Oriwa
Limited (2012 to 2016: 2243068, removed 2016, not 8160042 of 2021), Malachy
Properties Limited (2006, 2007: 1133623, removed 2010, not 8758427 of
2023), AMP Limited (2006: 853993, removed 2022, not 8695766 of 2023).
Judged today every one of these would be joined to the wrong company.

**Ten confirmed pairs off the donor views** (the row's name → the body):
mp_interests: Spire Investments Limited → 358292; Cameron Brewer
Communications Limited → 5718068; CGCA Jackson Limited → 3380713; Waipuke
Farming Limited → 8298020; Heartland Group Holdings → 6937955 (the one of
several live); Genesis Energy Limited → 936775 (the one of several live);
directors: Peel Forest Outdoor Pursuits Charitable Trust → trust board
655493; society officers: Bowls Orewa Inc → society 223215, Tauranga Indoor
Bowls Association → society 594273; charity officers: Public Trust → 926556,
The Lions Club of Invercargill South Incorporated → society 225674 (removed
2022, live at the 2014 appointment).

**Volume, time and memory.** The rule reads 3,339 rows and 1,178 bodies
and judges them in 1 s; the build's step is the same code over the same
rows, 2,632 confirmed and 1,182 near links where it stored 292 and 2,980,
so the links table and the build's time and memory do not move. The
groups gain the 2,340 newly confirmed rows (interests, officers, directors)
folded into their bodies' entities; `pub.entities` loses about that many
organisation entities.

## 13. The bodies' NZBNs, 30 October 2026 (fix-links-6)

Read-only on live through the session reader, before any change, against
`links.bodies` as the @3 build of 30 October left it (2,023,825 rows) and
the four published registers.

**The red item.** Check item 9's second line, "no NZBN names two bodies",
counts 2: `0000000000000` on 35 rows, 35 bodies (all charities; three of
them under a Companies Office trust board by their incorporation number,
32 their own body), and `9429049642469` on 2 rows, 2 bodies (CC58580,
registered 2020-11-09, deregistered 2023-02-20; CC61425, registered
2023-07-12 under a changed name; no Companies Office or society row
carries it; the two names key apart).

**The shapes.** `pub.charities.nzbn`: 29,893 of thirteen digits, 16,211
null, 35 all zeros, nothing else; the companies, societies and limited
partnerships registers publish no all-zero and no non-thirteen-digit NZBN.
Of the 46,139 charities none lacks a name or a registration date.

**NZBNs under several charity numbers.** 956 NZBNs on 1,944 charities rows
(two to four numbers each: deregistered on one day in 2008 and registered
again years later is the common shape). 955 of them already fold onto one
body, a Companies Office row by NZBN; one (above) did not. So the rule
"the charities of one NZBN are one body" moves one row today and holds
the 955 as they are.

**The new `BODY_SQL` on live** (read-only, 8 s): 2,023,825 rows, the same
count; 0 all-zero NZBNs (35 rows now carry none, every other row's NZBN
unchanged); 0 NZBNs on two bodies; CC61425's body is CC58580; one row's
body moved. No row of `links.rows` names either academy, no link touches
either charity number or any of the 35 placeholder rows, so the confirmed,
near and related counts do not move at the rebuild; check item 9's second
line becomes 0 and every item is green.

## 14. The courts lane's linking opportunities, 3 November 2026 (integrator, extract lists)

Counts only; no name, number, email, phone or address is written here. Read-only on live: `pub.links` as the last
build left it, and the courts identifiers of a full-corpus scratch build of the lane (3 November, 20:28 to 21:07, the
code released as ffdbf25: 16,794 records, 8,621 details on 3,269 documents) through the owner login, in a read-only
transaction. The register is `links/opportunities.py`.

**Names: rules today.** A court row's ref is `courts:<key>`; `/party/` keys are `pub.court_judgment_parties`,
`/person/` keys `pub.court_people`.

| View | Rule | Grade | Link ends |
| --- | --- | --- | --- |
| court_judgment_parties | name-only@1 | near | 4,099 |
| court_judgment_parties | full-name@1 | confirmed | 3,800 |
| court_judgment_parties | organisation-sole-company@3 | confirmed | 1,511 |
| court_judgment_parties | full-name@1 | near | 409 |
| court_judgment_parties | organisation-name@1 | near | 371 |
| court_judgment_parties | organisation-one-live-company@3 | confirmed | 81 |
| court_people | name-only@1 | near | 684 |
| court_people | full-name@1 | near | 184 |
| court_people | organisation-sole-company@3 | near | 36 |
| court_people | organisation-name@1 | near | 18 |
| court_people | organisation-one-live-company@3 | near | 4 |

The text reader's names confirm nothing (their own tier, `links.rows.MODEL_VIEWS`). **Sightings:** `pub.name_sightings`
holds 572,359 sightings on 14,859 court documents, so a judge's name, counsel's party and a case page's title are
covered wherever a register files the name.

**Identifiers: measure owed.** The details by kind (rows, documents, distinct values): address 3,439 / 1,496 / 2,938;
age 2,525 / 1,402 / 100; phone 1,130 / 698 / 329; email 800 / 449 / 463; PO Box 612 / 514 / 211; date of birth
55 / 42 / 55; vehicle registration 27 / 19 / 26; company number 20 / 11 / 20; NZBN 11 / 4 / 11; driver licence 1;
IRD number 1.

| Opportunity | Measured |
| --- | --- |
| NZBN → a body on its register | 11 distinct; 10 on `pub.companies`, 0 on societies, 0 on charities; 4 documents |
| company number → `pub.companies` | 20 distinct; 20 name exactly one company row; 0 more than one; 11 documents |
| email across documents | 463 distinct; 138 printed in two or more documents; 283 documents share one |
| phone across documents | 307 distinct (digits only); 123 in two or more; 585 documents share one |
| address across documents | 2,934 distinct (letters and digits only); 263 in two or more; 505 documents share one |
| PO Box across documents | 206 distinct; 76 in two or more; 429 documents share one |

Not yet read: how many shared emails, phones and addresses are a court registry's, a law firm's or an agency's (a
public office printed on every judgment of a registry) rather than a party's; the twenty pairs per opportunity come
before any rule. The numbers are a small join (NZBN and company number on 14 documents together); the emails, phones
and addresses are wide and mostly offices, to be measured by pair before any decision.

**Decisions owed to Arthur, one per opportunity** (no rule built, no private schema opened to the links lane):
1. NZBN and company number: confirm a judgment's party to the company whose number the judgment prints
   (`official-number@1`'s kind), with the numbers published to links alone or read privately.
2. Email and phone: whether one printed in two documents joins the names around them, near or confirming, once
   the offices are set apart.
3. Address and PO Box: whether one a judgment prints is matched to a company's registered office (a home address is
   never shown, hard limit 15).
4. Citation and case number: whether the links lane gathers a case's documents into one case entity, or the lane's
   own join (`case_links`, the suppression's reach) stands.

## 15. The views that print an official number, 3 November 2026 (integrator, the views the links never read)

Counts only; no name, number or address is written here. A scratch gather and link build on live
(`scratch_links_t1b`, 3 to 4 November, the code of this change) through the owner login. Arthur, 3 November 2026: "the
views the links never read, yes ... exact number joins come first".

Each view's printed number goes into `links.row_numbers` (ref, kind, value; `links.rows.NUMBERS`), and
`official-number@1` joins the row to the one body of `links.bodies` that holds it: an NZBN on any register, a company
number on the companies register's own companies, a charity number on the charities register. A number held by two
bodies, or by none, makes no link.

| View | Numbers printed | One body | Two or more | Held by none |
| --- | --- | --- | --- | --- |
| company_insolvencies (NZBN) | 109,586 | 109,586 | 0 | 0 |
| grant_recipients (charity number) | 15,116 | 15,111 | 0 | 5 |
| gazette_liquidations (company number) | 4,419 | 4,400 | 0 | 19 |
| company_lookup_holdings (NZBN) | 2,748 | 2,748 | 0 | 0 |
| retirement_villages (operator NZBN) | 409 | 409 | 0 | 0 |
| insolvency_companies (NZBN, company number) | 8 | 8 | 0 | 0 |
| overseas_investment_parties (company number) | 1 | 1 | 0 | 0 |
| fma_parties (company number) | 3 | 0 | 0 | 3 |

The verification that could fail: the body a number names carries the row's own name (organisation key) on 109,571
of 109,586 insolvencies and 4,323 of 4,400 liquidation notices. **The grants lane's NZBN is not read:** on
`pub.grant_recipients` the printed NZBN names a body of the row's name on 179 of 30,414 rows, while the charity number
does on 13,280 of 15,111; the NZBN is the funder's, or misplaced, and is a fault of the grants lane, not a join.

A row that a number confirms to one body is never confirmed by its name to another (`number_over_name`):
`organisation-sole-company@3` and `organisation-one-live-company@3` links of such a row to another body turn near
with `rules.NEAR_NUMBER_ELSEWHERE`; 110 did. `check.check_numbers` counts both in SQL apart from the build.

The organisation rules on the new views (rows with a body of their name; confirmed sole; confirmed one live of
several): company_insolvencies 109,556 / 99,828 / 9,155; grant_recipients 68,957 / 65,739 / 1,455;
gazette_liquidations 59,642 / 52,822 / 5,064; company_lookup_holdings 2,854 / 2,687 / 116; insolvency_companies
1,714 / 1,477 / 185; retirement_villages 973 / 319 / 0. Rows read: gazette_liquidations 61,017, insolvency_companies
2,540, company_insolvencies 212,780 (the company and each appointee its own ref), retirement_villages 1,007 (operator
and supervisor), grant_recipients 97,618, company_lookup_roles 12,652, company_lookup_holdings 18,487.

## 16. Ruling 1, a court party and the number its judgment prints, 3 November 2026 (integrator)

Arthur, 3 November 2026: confirm a court party to the company whose NZBN or company number its judgment prints. The
courts lane publishes `pub.court_company_numbers` (document, kind, value, page; kinds `nzbn` and `company_number`
only), the one view allowed to read `courts_private`, checked by the courts check to its exact statement.

`judgment-number@1` (`rules.judgment_numbers`) ties the number to a party, never to the document alone. Per document,
each number names its body through the same `number_target` as `official-number@1`; then:
- a party row (`court_judgment_parties` or `court_people`) whose name key is one of the body's names is **confirmed**
  to it; a row of the name of two numbered bodies is **near** to each (`NEAR_JN_TWO_BODIES`);
- with no such row, one numbered body and exactly one judgment-party name, the party is **near**
  (`NEAR_JN_OTHER_NAME`); a text reader's row alone never is;
- anything else is untied and makes no link.

Measured at §14 on a full-corpus scratch build of the courts lane: NZBN 11 distinct on 4 documents, 10 held on the
companies register; company number 20 distinct on 11 documents, each naming one company. On live the private table
fills at the courts load after this release; the links build that follows counts the outcomes (`numbers` in its
output: confirmed, other name, two bodies, untied). On the full scratch build (§18) the view was not yet
published, so the rule made no link (`{"view": "not published"}`); its first figures come from the links build after
the courts load.

## 17. Ruling 4, a case's documents gathered, 3 November 2026 (integrator)

Arthur, 3 November 2026: gather a case's documents into one case by citation and case number. `links.cases` (one row
per document of a case of two or more; published as `pub.court_case_documents`) is built from `pub.court_documents`
by `case-documents@1`: two documents are one case when they share a citation, a case number (`case_number_key`: upper
case, no spaces, leading zeros of a number part dropped) or a case page; a key shared by more than 60 documents
(`CASE_KEY_CAP`) joins none. A case is its smallest document. It is not an entity: it touches no link, group or
entity, so it never merges people or companies.

Keys on live (values; shared by two or more documents; the largest): case numbers 5,915 / 1,666 / 23; case pages
3,138 / - / 25; citations 10,024 / - / 6.

On the full scratch build (§18): 15,487 documents read, 2,067 cases of two or more documents holding 7,042 of them;
by kind, judgments 4,061, case pages 2,741, media releases 240 (a document counted once per case). Cases by size: the
largest 39 documents, then 29, 26, 23, 22, 19, three of 18 and three of 17. The largest carries 13 case numbers and 7
case pages: a judgment printing several proceedings' numbers (consolidated or related proceedings) joins their cases;
under the cap of 60 that is kept, and a case never joins people. 0.3 s.

## 18. The name views and the every-lane register, 3 November 2026 (integrator)

A full scratch build on live, `python -m links.build_all` into `scratch_links_full` (4 November, 00:13 to 01:47,
the code of this change, under `/usr/bin/time -v`): **5,636 s wall, 1,939,836 kB peak resident**, against the job's
7,200 s and 4 GB. The run shared the database with two orphaned scratch queries and other sessions' loads: its rows
stage took 3,606 s against 1,603 s for the same stage on 1 November, nearly all of it the model name checks of
`parliament_people` (about 2,030 s) and `court_people`; the views this change adds took 36 s to read. The links stage
took 541 s, name-only 190 s, watch 55 s, groups 90 s, entities 102 s, cases 0.3 s. The peak rose from 1,305 MB on
1 November.

Rows read, the new views: minister_diary_attendees 129,950 (298 set aside), building_practitioners 4,372,
council_meeting_attendance 4,618 and council_meeting_declarations 165 (rows no model read; `POLITICIAN_VIEWS`, so
full-name and name-and-address never confirm them), rea_parties 1,573, insolvency_people 17, grant_publishers 39, and
§15's number views. All rows 7,473,991 (live 6,869,167); groups 829,900 holding 3,736,532 rows (live 732,489 and
3,261,333); the largest group 32,157, unchanged; entities 3,360,336 (live 3,037,148).

Links by rule and grade, the new rules: `official-number@1` 132,747 confirmed (132,739 from a printed number, all
joining a body that holds it, no number naming two bodies: `check_numbers`); `licence-number@1` 210 confirmed, 31
near (names differ, or a person and an agency); `source-identifier@1` 415 confirmed (the company lookup's director
held key among them); name links turned near by a number 110. Link ends by view and grade, the new views (confirmed /
near): company_insolvencies 335,542 / 74,998; grant_recipients 88,998 / 15,024; gazette_liquidations 62,286 / 8,789;
company_lookup_holdings 24,526 / 11,207; minister_diary_attendees 15,482 / 78,805; company_lookup_roles 11,432 /
5,021; building_practitioners 8,653 / 18,253; insolvency_companies 1,666 / 296; retirement_villages 796 / 776;
rea_parties 584 / 996; insolvency_people 7 / 4; council_meeting_attendance 0 / 6,462; council_meeting_declarations
0 / 118; grant_publishers 0 / 47. `pub.company_lookup_roles` holds no body role today, so it prints no NZBN.

**The every-lane register.** `links.opportunities.view_problems` (run by `check.check_views`, `python -m
links.opportunities --views`): a published view with a text column named name, names, surname, nzbn,
company_number or charity_number (`VIEW_COLUMN`) that `links/rows.py`, the bodies, addresses and company names SQL,
the build or the lane's publish.sql never reads must be in `opportunities.EXCLUDED` with its reason; a view both read
and excluded, an exclusion with no reason, and an exclusion no longer naming anybody are problems too. On live: 0
problems. Excluded with a reason (`opportunities.EXCLUDED`): company_changes, company_lookups, company_states, society_states
(the same body as its pub.companies or pub.societies row, read as a body); court_cases (a case page's title: the
name sightings scan it and the case grouping gathers its documents); court_judgments (the court's name, not a party);
elections, linz_place_names, iwi_directory_settlements (an election's, a place's, a settlement's name); grants (each
recipient is its pub.grant_recipients row, read with its number); iwi_directory_relations (the related entity is its
own pub.iwi_directory_entities row); minister_diary_entries (the release's file name; the attendees are read);
parties, party_events, party_labels, party_names (the party lane's own entity); sanctions_lists (a list's name; the
listings are read). **Owed:** parliament_api_items (783 rows, a member's name: a fifth member-on-the-day view wants
Arthur's word); gazette_company_notices (1.55M rows, measured before it is read); linz_title_owners (5.7M rows: at
78 s a million to read and key, and 82% of owners individuals, it about doubles the rows and the union-find, which does
not fit the 7,200 s and 4 GB beside the rest; deferred).

## Track C: the review agent scored on the test pairs, 20 October 2026

Run `score-1` in `scratch_review` on the real published tables (`links.scores`,
`links.readings`), after candidate-returns published: 575 pairs, every one
the registers supply. The agent is `review-agent@2`: a screen on what the
registers state outright (a source identifier joins the pair; the two rows
file different middle names), then the review model (Qwen 3.6 35B-A3B, the
review profile, through the card the scheduler placed) under a verdict
grammar, 22.5 s a reading. A split is `not the same` or `contested`: both
take the link out of the walk that makes the groups.

| Truth | Band | Pairs | Not the same | Contested | No reason to doubt | Of which by the screen | Split per 100 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one person | rare | 137 | 0 | 0 | 137 | 135 | 0.0 |
| one person | middling | 7 | 0 | 0 | 7 | 7 | 0.0 |
| **one person** | **all** | **144** | **0** | **0** | **144** | **142** | **0.0 (wrongly split)** |
| two people | rare | 200 | 138 | 12 | 50 | 91 | 75.0 |
| two people | middling | 201 | 167 | 19 | 15 | 140 | 92.5 |
| two people | common | 30 | 25 | 0 | 5 | 19 | 83.3 |
| **two people** | **all** | **431** | **330** | **31** | **70** | **250** | **83.8 (caught)** |

**The two figures.** Wrongly split: 0 of 144 known-one-person pairs (0 per
100; the default pass mark is fewer than 1 per 100, so the run is recorded
as passed). Caught: 361 of 431 known-two-people pairs (83.8 per 100; 91.3
per 100 once the 61 pairs with an identical full name and middle name, whose
truth is not clean, are set apart).

**What the pass does and does not show.** 142 of the 144 one-person pairs
are a seat and its winning candidacy, joined by the house lane's own
identifier, and the screen passes those without asking the model; only 2
one-person pairs (a candidate across an original and an amended return)
reached the model, and it kept both. So the model's own rate of wrongly
splitting one person is measured on 2 pairs, which is no measurement. The
registers hold no other one-person kind yet (card
`three-test-pair-kinds-the-registers-cannot-supply`); the charities officer
identifier was expected to supply hundreds once a charities lane published;
it supplies none (section 10: it keys a row, not a person), and the switch
stays off.

**The model alone**, on the 181 two-people pairs the screen left it: 111
caught (61.3 per 100; rare 54.1, middling 75.4, common 54.5), 70 kept. Its
misses are two directors of one name on one company at once, where it read
the shared company and office as joining the two rows ("the differing
appointment dates likely reflect a single person re-appointed"), though the
evidence states `same_role_on_same_body_at_once`. The evidence derives that
field from the same fact that defines the pair kind, so the screen was kept
from deciding on it: the figure measures whether the model follows the
register's practice when told it, and it does so three times in five.

The run spanned two restarts (the card was lent to a read-pages job midway);
nothing that decides a verdict changed between them, and the fingerprint in
`links.scores` is of the judgment as it stands. No web search: the gate has
no search route (card `the-fetch-gate-has-no-search-route`). Nothing was
applied: `links.SETTINGS["review_applies"]` is off and `check.py` holds it.

## 15. Rulings 2 and 3 researched: a shared email or phone, and a judgment's address against a registered office, 4 November 2026 (integrator)

Measurement only; no rule built, nothing applied. Counts only: no email, phone, address or name is written here.
Read-only on live through the owner login (the private schema), in a read-only transaction: `courts_private.identifiers`
as the 04:40 load left it (4 November, finished 05:31: 9,709 details; 6,531 of the four kinds below on 2,230
documents), `pub.court_people` (who sits in each document), `pub.companies` and `pub.company_addresses` (892,803
registered offices). The text around each detail is read on its own page only (2,230 known documents, none
unreadable), never the store wholesale. The page: `docs/research/contact-details-2026-11-04.md`.

**How a value is sorted.** An email by its domain: courts, tribunals and government (`govt.nz`, justice, police,
crownlaw, `.ac.nz` and the like); a law firm (law, legal, lawyer, barrister, chambers in the domain, or the domain's
stem in a counsel firm's name in the same document, or a webmail address whose local part carries counsel's surname);
personal webmail (gmail, xtra and 40 more); a company (the domain's stem is a company's name key in `pub.companies`,
suffixes off, four letters or more); other. A phone (digits, national form) and an address or PO Box by the 400
characters before it on its page: a registry heading (registry, registrar, case manager, courthouse, DX, a named
tribunal) or, printed in five or more distinct cases, the word court or tribunal; then a law firm's words
(solicitors, barristers, counsel, for the applicant …); a toll-free phone; recurring with no heading; the rest.
An address is matched to a registered office by its street (number after any unit's slash, street name, type, the
lane's abbreviations) and, where the judgment prints one, its town agreeing with the office's lines.

**Emails** (496 distinct; 142 in two or more documents):

| Category | Distinct | In 2+ documents | Documents | Person names (parties, witnesses, others) | All person names |
| --- | --- | --- | --- | --- | --- |
| courts, tribunals, government | 99 | 26 | 133 | 1,158 | 1,752 |
| law firms | 95 | 34 | 111 | 163 | 512 |
| companies | 111 | 36 | 141 | 776 | 1,166 |
| personal webmail | 48 | 2 | 41 | 765 | 1,025 |
| other (no category matched) | 143 | 44 | 187 | 1,252 | 2,044 |

**Phones** (304 distinct; 120 in two or more documents):

| Category | Distinct | In 2+ documents | Documents | Person names | All person names |
| --- | --- | --- | --- | --- | --- |
| courts, tribunals, government (a registry heading, or recurring in 5+ cases beside court) | 69 | 42 | 509 | 1,518 | 2,415 |
| government context (an agency's words) | 20 | 9 | 26 | 165 | 271 |
| law firms | 136 | 59 | 121 | 363 | 856 |
| toll-free | 7 | 2 | 9 | 28 | 63 |
| other | 72 | 8 | 63 | 433 | 558 |

**Addresses** (3,301 distinct by the lane's address key; 314 in two or more documents) **and PO Boxes** (206; 79):

| Category | Addresses | In 2+ | Documents | Person names | PO Boxes | In 2+ | Documents | Person names |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| court or registry | 84 | 32 | 255 | 980 | 49 | 28 | 355 | 1,297 |
| law firm context | 394 | 58 | 377 | 2,622 | 111 | 43 | 124 | 724 |
| a registered office, street and town agree | 334 | 28 | 302 | 1,876 | 5 (box number) | 1 | 5 | 37 |
| a registered office, street only | 653 | 60 | 430 | 3,070 | | | | |
| recurring, no heading | 3 | 3 | 18 | 233 | 2 | 2 | 18 | 135 |
| neither (likely a person's) | 1,833 | 133 | 887 | 5,739 | 39 | 5 | 42 | 335 |

**What ruling 2's rule would yield** (the emails and phones not an office's: companies, webmail and other emails;
other phones), printed in two or more documents:

| | Values | Document pairs | Across different cases | Person names in them | Pairs sharing a person name | Pairs sharing none | Cross-document name pairs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| email | 82 | 495 | 467 | 1,239 | 167 | 328 | 41,417 |
| email, companies apart | 46 | 240 | 217 | 954 | 68 | 172 | 9,988 |
| phone | 8 | 11 | 11 | 40 | 5 | 6 | 11 |

Joining every name beside a shared email would join 41,417 pairs of names out of 495 document pairs: the value is not
yet anyone's (`courts_private.identifiers.person` is empty until the model item). Personal webmail barely recurs (2
of 48).

**What ruling 3's rule would yield** (every address whose street is a registered office's, before the categories
above):

| Match | Values | Documents | Of them, a body of the document carries the company's name |
| --- | --- | --- | --- |
| street and town, one company | 170 | 167 | 5 |
| street and town, 2 to 5 companies | 135 | 143 | 28 (of the 270 with several) |
| street and town, over 5 companies (a busy office) | 135 | 165 | |
| street only, one company | 332 | 248 | 7 |
| street only, 2 to 5 / over 5 | 296 / 144 | 272 / 157 | 37 (of the 440 with several) |

427 of the 440 street-and-town matches are a company's current office (`in_latest`).

**The rule each ruling would need** (Arthur's to rule; ruling 106's method: these counts, then twenty pairs):

1. **Ruling 2, a shared email or phone** (`shared-contact@1`, proposed). Two court person rows are joined when one
   email (lower case) or phone (national digits) is printed in both documents, the value is not an office's (not a
   court, tribunal, agency or law-firm domain or heading; not toll-free; not printed in five or more cases), and the
   value is the person's: the model item's `person` on the identifier, never every name beside it. Confirmed only
   where the two rows' names agree (email 167 pairs, phone 5: the value corroborates a name link); near where they
   differ (email 328, phone 6: one contact, two names); a company's email joins the company, not its people. The
   links lane reads `pub.*` only, so the rule reads the values privately (`links_private`) or by a keyed hash.
2. **Ruling 3, a judgment's address to a registered office** (`judgment-address-office@1`, proposed). A street address
   a judgment prints, not a court's, registry's or law firm's, is matched to `pub.company_addresses` by street core
   and agreeing town, to one company only (a busy office, over five companies, never). Near alone (an address never
   confirms, keys/addresses.py): 170 values; confirmed only with a party of the judgment carrying the company's name
   by the organisation rules (5). Street-only matches (332 to one company) wait for a town. The 1,833 addresses that
   match no office are likely persons' and are never matched, shown or exported (hard limit 15).

## 16. Ruling 3 widened: the judgment addresses matched privately on four sides, 4 November 2026 (integrator)

Arthur, 4 November 2026: "match them. remember this is not a product yet." Counts only; no address or name is
written here. In scope: the judgment addresses §15 sorted as neither a court's, a law firm's nor an office's, and
those matching an office's street only: 2,763 identifier rows on 1,129 documents. Every side is read by the one
reading, `keys.addresses.street_parts` (unit, number, street, type, the places after it) and `keys.addresses.meet`
(the strongest level shared; never across two places none shared, nor two different units). A session measurement
through the owner login (it reads four lanes' private schemas, which no module may); the script is
`/home/user/querynzv4-work/scratch/integrator-9d788fb/address_matches.py`. The matches, refs only, are in
`scratch_address_matches_private.matches` (side, identifier key, document, target ref, level, name shared, how), and
twenty per side, those sharing a name first, in `scratch_address_matches_private.samples`; neither the reader nor the
product login sees the schema. LINZ is read from the scratch build of the title addresses (`scratch_linz_addresses`).

| Side | Judgment addresses matched | Documents | Targets | Matches | Of the addresses, best at unit / place / street only | Sharing a name: addresses / documents / targets | Sharing a name, at place or unit level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LINZ titles (owners' names) | 2,246 | 949 | 7,204 titles | 91,950 | 15 / 720 / 1,511 | 342 / 217 / 318 titles | 117 |
| other judgments | 554 | 296 | 637 identifiers | 1,191 | 4 / 139 / 411 | 346 / 170 / 394 | 86 |
| insolvency estates (address at adjudication) | 33 | 33 | 43 estates | 47 | 0 / 4 / 29 | 0 / 0 / 0 | 0 |
| company registered offices | 557 | 352 | 4,325 companies | 4,880 | 0 / 13 / 544 | 28 / 26 / 32 | 0 |

A name is shared when an owner of the title (person or corporate key), the estate's name, the company's name, or a
person of the other judgment is among the judgment's parties, witnesses and others (judges and counsel apart). Most
judgments print a street without its town, so most matches are at the number-and-street level, which names the same
street in many towns: 2,246 addresses reach 7,204 titles.

**The rules this would need** (Arthur's to rule after twenty pairs; the samples table holds them):

| Rule (proposed) | Confirmed | Near | None |
| --- | --- | --- | --- |
| `judgment-address-title@1` | place or unit level and an owner's name among the parties (117) | place or unit level alone; street only with an owner's name (225) | street only, no name |
| `judgment-address-judgment@1` | place or unit level and a shared person (86) | place or unit level alone; street only with a shared person (298) | street only, no name |
| `judgment-address-insolvency@1` | place level and the estate's name (0) | place level alone (4) | street only |
| `judgment-address-office@1` (§15) | the company's name among the parties | one company, street and town | a busy office; street only |

**How it would run.** No module may read two lanes' private schemas (tests/test_imports_one_way.py), and the links
lane reads `pub.*` only. The fit is a keyed hash: each lane's load writes a hash-only row per address and level
(ref, level, HMAC of the `street_parts` key) into a `pub` view, and the links lane joins the hashes and writes the
links into `links_private`. An unkeyed hash is no protection (NZ Addresses, layer 123113, is a public list to hash
against), so the key is a secret Arthur places in the credentials folder; until then the matching stays this
measurement.

## 19. Ruling 142: the private-value rules and the LINZ owners built, 4 November 2026 (integrator)

Ruling 142 (Arthur, 4 November 2026): no sample pairs, the §15 and §16 rules built now; privacy is applied at a
product's export. The hash-key design of §16 is dropped.

**How the links read a private value.** A fixed schema `pub_private` (support/db `FIXED`, private by its suffix, so
neither `qv4_read` nor `qv4_product` is granted it) holds views each lane declares and owns in
`registers/<lane>/pub_private.sql`: `court_identifiers` (courts_private.identifiers, the address, PO box, email and
phone kinds), `insolvency_addresses` (the address at adjudication), `linz_title_addresses` and
`linz_title_address_points`. `support.db.private_views` remakes them, one savepoint each, skipping a view whose lane
table is missing (a lane's load drops its tables with CASCADE); it runs at `db apply` and at the head of the links'
identifiers step. Only the links lane and support/db may name the schema (tests/test_imports_one_way.py). The links
rows carry no value: their evidence keys are held to `check.IDENTIFIER_EVIDENCE`; the value, its kind, level and
category go in `links_private.identifier_links`, one record per link end (`check_identifier_links`: every such link
has its record).

**The rules** (links/rules.py, links/identifiers.py), counts from the full scratch build into `scratch_links_priv`
(code at 68c65cd), as judged and after the model tier turns to near every link touching a row a model read
(`court_people`):

| Rule | Judged confirmed | Judged near | After the model tier: confirmed / near |
| --- | --- | --- | --- |
| `judgment-address-title@1` | 0 | 0 | 0 / 0 (the LINZ title addresses are not yet loaded: linz_private empty) |
| `judgment-address-judgment@1` | 271 | 982 | 74 / 1,179 |
| `judgment-address-insolvency@1` | 2 | 1 | 1 / 2 |
| `judgment-address-office@1` | 47 | 38 | 26 / 59 |
| `shared-contact@1` | 53 | 26 | 0 / 79 |

6,912 identifiers on 2,638 documents read; 3,052 private records. The courts' `person` field is empty on every
identifier, so every tie is the party name printed nearest (within 1,000 characters); a judgment-party row is
preferred to a `court_people` row, but most ties land on `court_people`, which is why the model tier turns all of
`shared-contact@1` to near. Offices (courts, agencies, law firms, toll-free numbers, a value printed in 5 or more
cases) make no link. The step took 151 s.

**The LINZ owners as rows.** `pub.linz_title_owners` is read as a row source (5,745,217 rows, 4,946,519 people, none
set aside), by the existing name rules. All rows 13,877,607 (live 7,382,205); links 11,130,011 (live 4,189,284).
Links touching a LINZ row: `full-name@1` 2,445,149 confirmed (1,189,086 of them owner to owner) and 24,079 near;
`name-only@1` 488,200 near (147,669 owner to owner). `full-name@1` in all is 4,369,493 (live 1,458,955) and
`name-only@1` 3,488,243 (live 873,231). No organisation rule joined a LINZ corporate owner. Groups 1,470,665 holding
6,836,020 rows (live 732,489 groups), the largest 32,157 unchanged, contested 42,997; entities 6,685,712 (live
3,037,148), 40 politician entities holding a LINZ row. A full name confirming owner to owner across titles makes
large groups of common names; the watch flags 117,999 of 5,024,168 watched.

**Time.** The nightly of 4 November (queue row 1439, 07:45) was stopped at its 7,200 s deadline and published
nothing: the rows stage reached `hansard_people` by 07:55, and `model_check` of `parliament_people` then read each of
63,256 documents' text by its own query on `pub.parliament_written_questions` until 09:45. It now reads them in
batches of 20,000 (`model_check.BULK`, e998079): about 40 s. The full scratch build, under the courts load's and the
sightings' writes: **6,348 s wall, 5,668,740 kB peak resident**. Rows 3,247 s (the LINZ owners 1,740 s of it;
directors 463 s against 211 s on live, the write contention); links 1,831 s (full-name 359 s, name-only 599 s, the
model tier about 190 s); watch 82 s; groups 205 s; entities 199 s; the measurements 748 s. The LINZ owners are kept
across a refill while `max(loaded_at)` is older than the last gather and the reading's code is unchanged
(`rows.STEADY`, `rows_catch.fingerprint`), so only the first build after a LINZ load reads them. The reader ends its
transaction after each view and each stage (68c65cd), so a lane's DROP ... CASCADE no longer waits on the build.
qv4-links-build is set to `deadline_s = 10800` and `memory_gb = 6.5`.
