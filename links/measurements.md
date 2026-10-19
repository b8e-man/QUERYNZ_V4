# The six first measurements (plan 4.2), 20 October 2026

Run on the real published tables through `python -m links.measure`; the
figures are in `links.measurements` (JSON) and summarised here. Nothing
here comes from the sample. Bands: a first-and-last name carried by 1 to 5
director rows is rare, 6 to 50 middling, over 50 common.

## 1. How often a full name repeats

| Band | First-and-last names | Director rows | Rows with a middle name | Names on one row only |
| --- | --- | --- | --- | --- |
| rare | 529,892 | 794,935 | 534,110 | 368,213 |
| middling | 26,933 | 309,743 | 235,254 | 0 |
| common | 868 | 80,900 | 68,111 | 0 |

Full names with a middle name: 471,356 names on 837,485 rows; 130,376
names repeat (496,505 rows); the most repeated carries 662 rows. Without a
middle name: 213,909 names on 348,164 rows; 52,966 repeat (187,221 rows);
the most, 648. Of the other registers' rows, the share whose first and last
name is also on the director register: shareholders 85%, society officers
44%, liquidators 67%, candidates 44%, members 47%, MPs' returns 48%,
donors (Part A) 58%, disclosures 71%, promoter people 46%.

## 2. Addresses shared by many companies

| Companies at the registered office | Addresses | Companies |
| --- | --- | --- |
| 1 | 351,139 | 351,139 |
| 2 to 5 | 89,549 | 222,316 |
| 6 to 50 | 8,161 | 101,969 |
| 51 to 200 | 912 | 88,528 |
| over 200 | 276 | 102,688 |

1,188 busy addresses (over 50 companies) hold 191,216 companies, 22% of
all. The busiest holds 2,463.

## 3. The error rate of the two confirming rules

On the test pairs (`links.pairs`, seed 43). Error on a "two people" pair
means the rules confirmed it; on a "one person" pair, that they did not.

| Kind | Truth | Band | Pairs | Confirmed by rule 1 | By rule 2 | Error rate | Of which identical full name with middle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| two directors, one name, one company at once | two people | rare | 200 | 43 | 61 | 52.0% | 43 |
| | | middling | 200 | 12 | 31 | 21.5% | 12 |
| | | common | 30 | 6 | 5 | 36.7% | 6 |
| two candidates, one name, different electorates | two people | middling | 1 | 0 | 0 | 0% | 0 |
| a seat and its winning candidacy | one person | rare | 135 | 0 | 0 | 0% (joined by the lane's own identifier; the name rules never confirm a politician) | 14 |
| | | middling | 7 | 0 | 0 | 0% | 0 |

Two caveats on the "two people" kind. Rule 2 confirms two roles on one
company by that company's own office, so a same-company pair is confirmed
by construction (queued for Arthur: `does-one-company-s-office-count-as-a-
shared-address`). And a pair with an identical full name and middle name on
one company may be the register listing one person twice (a re-appointment
kept beside the first row), so that part of the truth is not clean; those
pairs are counted in the last column. Without them: rare 30.5%, middling
15.5%, common 16.7%, all by rule 2 on the shared company.

The review agent's reading of 100 confirmed links drawn at random (seed 7):
98 "no reason to doubt", 2 "contested" (common names on trustee companies in
different cities, nothing joining them). This is an agent's judgment of the
evidence, by the links session (Fable 5.1) from the registers alone, with
no web search; the local review model's job is built (`links.review --run`)
and waits on the catalogue. Nothing was applied.

## 4. How often each rule can fire, per register

| Register, view | Rows | Rule 1 can compare a middle name | Rule 2 has a company address | Politician (never confirmed by name) |
| --- | --- | --- | --- | --- |
| companies, directors | 1,185,805 | 837,604 | 1,185,805 | 0 |
| companies, shareholders (individuals) | 1,376,457 | about 1.0 M | 1,376,457 | 0 |
| societies, officers | 133,003 | 48,534 | 0 (no society address published) | 0 |
| gazette, liquidators | 45,065 | most | 0 | 0 |
| mp_interests, returns | 2,526 | 0 | 0 | 2,526 |
| house, candidates and members | 1,854 | 0 | 0 | 1,854 |
| party_returns, donors (people) | 536 | few | 0 (no donor address published) | 0 |
| disclosures (people) | 359 | few | 0 | 0 |

Links made: rule 1 1,257,095 (companies to companies 1,213,025; to
societies 15,962; to gazette 12,557; gazette to gazette 13,514; to
disclosures 51); rule 2 942,014 (all within companies: 573,440 a director
and a shareholder of one company; 176,947 directors across companies;
135,186 director to shareholder across companies; 44,995 shareholders;
259 two directors of one company); the number 4,384; the lane's own join
142; organisation names 191 (near); name-only near 410,160.

## 5. Company names to official numbers

| Register | Organisation donors | Exactly one company alive on the date | Several | Name held, none alive | No company of that name |
| --- | --- | --- | --- | --- | --- |
| disclosures | 150 | 94 (63%) | 0 | 1 | 55 |
| party returns (Part A) | 136 | 72 (53%) | 0 | 1 | 63 |

## 6. The shape of the groups

669,863 groups over 2,251,437 rows; 51,618 contested by the watch (149,982
of 2,199,109 confirmed links flagged: 141,447 regions apart, 8,549 a very
common name without a middle name); no group contradicts a `not the same`
decision (there are none yet).

| Rows in the group | Groups | Rows | Contested | Spanning registers |
| --- | --- | --- | --- | --- |
| 2 | 438,555 | 877,110 | 6,717 | 6,332 |
| 3 to 5 | 164,017 | 610,731 | 23,392 | 8,712 |
| 6 to 20 | 62,642 | 528,569 | 18,977 | 3,693 |
| 21 to 100 | 4,237 | 157,985 | 2,308 | 673 |
| over 100 | 412 | 77,042 | 224 | 106 |

The largest, 1,220 rows across companies, Gazette and societies, is a
professional trustee director; the next two are liquidators named on
hundreds of notices.
