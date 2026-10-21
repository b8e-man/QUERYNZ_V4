# tender-awards: known limits and the checkpoint

Step 6.2, template 1 (use case 10, tender and award intelligence), on the
GETS award notices (`registers/tenders`, merged as tenders-1). For a
supplier, every award it won: the agency and the RFx ID (the notice's
title), the award date, the value as published, the categories. For an
agency, the same lines read by the agency (the title of the award step and
the CSV's `award` column; the page filters by grade only: card
`the-scan-page-filters-by-grade-only`). The company row each supplier is
joined to, by business number (confirmed) or else by name alone (near,
the reason on the line), every company under that name a line of its own
marked as one of its namesakes; a supplier with no company found is
listed with the company step "none found in pub.companies by business
number or by name".

## Known limits

The template's `limits` (on the page and in `answers.json`) are the full
list. In short:

- **No business number joins today.** The supplier file publishes none a
  join can use (12,694 in exponent form, the rest empty, NULL or short).
  Every company line is near. 1,055 supplier rows carry a 5-to-7-digit
  value; 1,032 of them are a Companies Office company number, and for 869
  the first letters of the two names agree; the template does not use it (card
  `the-gets-supplier-number-is-often-a-company-number`).
- **A name is a namesake of record**, never an identity. Trading names,
  misspellings and overseas suppliers meet nothing; a removed company
  under the same name meets as a namesake (Fulton Hogan, 1935 to 1995).
- **The value is the notice's**, as published: `0` means no value given
  (the value note says so); the historic file (2014 to 2019) has no
  amount column. Nothing is summed.
- **A notice is shown by its agency and RFx ID**, never its title: 754 of
  the 29,874 titles carry a street address, which can be a home (card
  `award-notice-titles-carry-street-addresses`).
- **No address is read.** The company's registered office is read by the
  shape only to flag a thousand-company office, never printed.
- **"Confirmed" here** means the award and the supplier are joined by the
  register's own key and no company was joined (8,567 lines): no line is
  confirmed by a business number today.

## Checkpoint (21 October 2026, node2)

Run on the real published tables, the state in the sample database's
scratch schema (`QV4_SCAN_STATE=querynz_v4_sample/scratch_scan_templates_1`),
with the shape's additions applied on a merged copy
(`_shape/scan-templates-1-shape.diff`). Run 18: **33,744 lines in 17.5 s**
(one start, one query); 25,177 near, 8,567 confirmed (no company found), 0
contested; 73 lines with a hub; 61,722 citations; 0 problems. Views as
loaded: award_notices and award_suppliers 2026-10-21 21:00, companies
2026-10-21 13:33.

Read back: every one of the 31,264 suppliers the notices name is listed
(22,964 notices); 20,596 suppliers meet one company, 2,101 meet 2 to 6
namesakes (4,581 lines), 8,567 meet none. The check's read-back on 60
lines spread across the run holds (supplier on the notice, names fold
alike, namesake counts recounted); the SQL fold equals the check's fold on
400 real names. `python -m products.scan check` green (11.6 s, all five
scans).

## Twelve lines read by eye (run 18)

| n | grade | award (agency · RFx, date, value as published) | supplier | company | seen |
| --- | --- | --- | --- | --- | --- |
| 26041 | confirmed | Orion New Zealand · 33828231, 18 May 2026, 0 (no value given) | Ventia Nz Operations Limited - CHCH Distribution | none found | a branch suffix defeats the name |
| 10037 | confirmed | New Zealand Blood Service · 25059326, 11 Jan 2022, 0 | Arrowsmith & Grant (Australia, 11-digit number) | none found | overseas, right |
| 28716 | confirmed | Internal Affairs · 17994334, 26 Jan 2018, historic: no amount | Royal NZ Foundation of the Blind trading as Access Advisors | none found | a charity, not a company: right |
| 2811 | confirmed | Internal Affairs · 21693478, 1 Jul 2020, 0 | Beamafilm | none found | a trading name |
| 4231 | near | Education - School Infrastructure · 22381512, 6 Feb 2020, 290,759 | SSC HOLDINGS LIMITED | SSC HOLDINGS LIMITED, removed 2014; one of 2 | the namesake marking is what shows the removed one |
| 31213 | near | Government Property Group · 19595804, 11 Oct 2018, historic | AR Consultants Limited (7 digits 3800256) | AR CONSULTANTS LIMITED, removed 2009; one of 3 | the company number would settle it |
| 5249 | near | NZTA (historic) · 22967459, 23 Sep 2020, 1,164,301 | Fulton Hogan | FULTON HOGAN LIMITED 1935 to 1995; one of 2 | the old namesake, marked |
| 20693 | near | NZTA (historic) · 30701972, 20 Dec 2024, 1,010,010 | FULTON HOGAN LIMITED | FULTON HOGAN LIMITED, registered 1952; one of 2 | the live one, marked |
| 30617 | near | Christchurch City Council · 19242842, 26 Apr 2018, historic | Grounds & Services Ltd | GROUNDS & SERVICES LIMITED, registered 2015 | "Ltd" folds to "Limited": right |
| 3232 | near | Education - School Infrastructure · 21909344, 28 Feb 2020, 0 | MCM CONTRACTING LTD | MCM CONTRACTING LIMITED | right |
| 25747 | near | Education - School Infrastructure · 33523675, 25 May 2026, 148,534 | MR FENCER NZ LIMITED | MR FENCER NZ LIMITED, registered 2025 | right |
| 11550 | near | Primary Industries · 25773030, 29 Aug 2022, 0 | The Training Practice | THE TRAINING PRACTICE LIMITED | a name without its ending meets: near, right |
