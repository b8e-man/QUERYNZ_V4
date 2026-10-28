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
identifier will supply hundreds once a charities lane publishes, and the
switch should stay off until the model has been scored on them.

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
