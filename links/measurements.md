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
