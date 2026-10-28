# fix-links-1: `organisation-one-live-company@1`, ruling 107 (30 donation rows to 18 companies)
branch: fix/links-1 (pushed, 397f0ad; one commit on main's 6ea84b2)
session: fix-links-1 (Opus, fix weight, scope links/)
raised: 2026-10-28
claims: links/ (rules.py, build.py, check.py, measure.py, pairs.py, review.py, spec.md, README.md, measurements.md, tests/test_rules.py); docs/decisions/queue/ (one item removed); one lesson, lessons/INDEX.md; docs/status/links.md

## The rule

`rules.one_live_company(row, companies)`, pure, beside `sole_company`, which
hands it any name several companies carry. "Live in the year" is ruling
106's: registered by the year's end, not removed before its start; a dated
declaration is a year of one day. Exactly one live: that pair is
**confirmed** under `organisation-one-live-company@1`; each other company of
the name stays near under `organisation-name@1`, "this one was not live in
the donation's year, and the one that was is confirmed". None live, or more
than one: every pair near, the reason saying "none of them" or "more than
one of them was live". Evidence on every pair: the donation's date and year,
`companies_considered` (number, name, registered and removed dates, live or
not, for each), `live_in_year` (the number of the one, or null),
`companies_alive_on_date`. `build.sole_company_links` stores what it returns;
nothing else in the build changed.

## Measured (scratch on the live tables)

`scratch_fix_links_1` in querynz_v4: rows gathered once from `pub` (2.86 M,
nineteen views), the 5,694 live decisions copied in, built with main's code
(before; equals links-3's after) and with this rule (after) over the same
rows.

| | groups | rows in groups | contested | largest |
| --- | --- | --- | --- | --- |
| before | 681,815 | 2,315,735 | 52,085 | 1,220 |
| after | 681,832 | 2,315,782 | 52,085 | 1,220 |

30 donation rows have a name several companies carry; all 30 have exactly
one live in the year (0 with none, 0 with two). **30 confirmed, to 18
companies.** The other 40 pairs stay near. `organisation-name@1` "several
companies" 792 → 722 (the rest are declared interests, unchanged). The 48
rows (30 donations, 18 companies): 1 in a group before, 48 in 18 groups
after, none contested.

## Every confirmed pair

Donor as filed (register) → company, number, year (a dated declaration by its day).

1. Breeze Construction Limited (party return) → BREEZE CONSTRUCTION LIMITED, 7867079, 2025
2. Buen Holdings Limited (declaration) → BUEN HOLDINGS LIMITED, 1638183, 2023-07-10
3. Christopher & Banks Limited (declaration) → CHRISTOPHER & BANKS LIMITED, 3482091, 2023-03-13
4. Christopher & Banks Limited (party return) → CHRISTOPHER & BANKS LIMITED, 9321019, 2025
5. Christopher & Banks Limited (declaration) → CHRISTOPHER & BANKS LIMITED, 9321019, 2026-04-29
6. Christopher & Banks Limited (declaration) → CHRISTOPHER & BANKS LIMITED, 9321019, 2026-04-29
7. Christopher & Banks Ltd (declaration) → CHRISTOPHER & BANKS LIMITED, 3482091, 2022-05-12
8. Christopher & Banks Ltd (party return) → CHRISTOPHER & BANKS LIMITED, 3482091, 2023
9. Christopher & Banks Ltd (declaration) → CHRISTOPHER & BANKS LIMITED, 3482091, 2023-06-13
10. Clean as a whistle Ltd (party return) → CLEAN AS A WHISTLE LIMITED, 1304408, 2023
11. Counties construction limited (party return) → COUNTIES CONSTRUCTION LIMITED, 8260201, 2025
12. Grande Construction Limited (party return) → GRANDE CONSTRUCTION LIMITED, 5480321, 2023
13. Hero Limited (party return) → HERO LIMITED, 5510728, 2023
14. Hero Limited (party return) → HERO LIMITED, 5510728, 2023
15. Lewis Holdings (declaration) → LEWIS HOLDINGS LIMITED, 42464, 2016-11-07
16. Little Umbrella Limited (declaration) → LITTLE UMBRELLA LIMITED, 7431656, 2026-09-23
17. Matrix Consulting Limited (party return) → MATRIX CONSULTING LIMITED, 1808290, 2022
18. Matrix Consulting Limited (party return) → MATRIX CONSULTING LIMITED, 1808290, 2022
19. NZ Made (party return) → NEW ZEALAND MADE LIMITED, 1474459, 2025
20. Oregon Group Limited (party return) → OREGON GROUP LIMITED, 560422, 2023
21. Oregon Group Limited (declaration) → OREGON GROUP LIMITED, 560422, 2023-08-08
22. Oregon Group Limited (party return) → OREGON GROUP LIMITED, 560422, 2025
23. Oregon Group Limited (party return) → OREGON GROUP LIMITED, 560422, 2025
24. Owens Properties Limited (declaration) → OWENS PROPERTIES LIMITED, 7696116, 2023-09-01
25. Profile Management Limited (party return) → PROFILE MANAGEMENT LIMITED, 9000075, 2025
26. Progressive Construction Limited (declaration) → PROGRESSIVE CONSTRUCTION LIMITED, 1548787, 2026-08-13
27. Progressive Construction Ltd (party return) → PROGRESSIVE CONSTRUCTION LIMITED, 1548787, 2025
28. Tawata Farms Limited (declaration) → TAWATA FARMS LIMITED, 1818345, 2021-08-20
29. Tawata Farms Ltd (party return) → TAWATA FARMS LIMITED, 1818345, 2021
30. Wilson Contractors (party return) → WILSON CONTRACTORS LIMITED, 1500356, 2025

In every case but one, the companies not chosen were removed years before
the gift (Hero Limited's three others by 2014; Matrix Consulting's two by
2005). **Worth a look on the board:** Christopher & Banks Limited is two
companies, 3482091 (registered 2011, removed 2024-12-18) and 9321019
(registered 2025-03-06). The rule puts the 2022 and 2023 gifts on the first
and the 2025 and 2026 gifts on the second, so the donor shows as two
entities. They are not joined to each other: neither name carries a year in
brackets, so `successor-name@1` does not reach them. "Lewis Holdings"
(2016-11-07) is before the 2017 window; it is joined like any other row.
"NZ Made" and "Wilson Contractors" were filed with no legal ending.

## Checks and tests

- `check.py` check 7, counted in SQL apart from the Python: no donation row is
  confirmed by name (either rule) to a company not live in its year, or where
  two companies of the name were live; no one-live link has only one company
  of its name. On `scratch_fix_links_1` (`--pub scratch_fix_links_1_pub`):
  **34 of 34 green**. In a transaction, rolled back, each planted fault
  turned check 7 red: the linked company registered after the year (1), a
  second company of the name made live (4), a ruling 106 link relabelled as
  this rule's (1).
- Measurement 8 (`measure.py`, `measurements.md`).
- Test pairs (`pairs.py`): new kind `donor-and-company-not-live`, truth "two
  people" (two bodies: a company not live in the year gave nothing then).
  63 drawn, 63 measured, 0 confirmed, 0 in one group. Measurement 3 judges
  this kind with `rules.sole_company`, because the company is not a row in
  `links.rows`. Without that it would have skipped all 63 without a word
  (the lesson filed). The review agent reads people, so `review.score`
  leaves this kind out (`pairs.ORG_KINDS`).
- `test_rules.py`: the rule's confirmed, other-live, none-live and two-live
  cases, and the day boundaries. Fast tier, links
  (`QV4_INTEGRATOR=1 bin/fast links`): **green in 45.8 s**.

## For the integrator

- After the merge, run **`qv4-links-build`**. It carries links-3's rules
  as well; when this session began (about 12:30), live `links.links` still
  held the build from before links-3. No table or view changes: `tables.sql` and `publish.sql` are untouched.
  After the build, run `check.py` live.
- Installer: nothing. `support/db`: nothing.
- Queue: `one-company-of-several-live-in-the-donation-s-year` deleted (answered
  by ruling 107). `docs/decisions/queue.md` still lists it, and it is outside
  this fence, so rebuild the queue at the merge.
- Lesson: `a-test-pair-whose-end-is-not-a-row-is-skipped-by-a-measure-that-looks-up-rows`
  (index regenerated). No card.
- Drop `scratch_fix_links_1` and `scratch_fix_links_1_pub` in querynz_v4
  (and the sample fill's `scratch_fix_links_1` in querynz_v4_sample) on
  Arthur's word.
- Hard limit 14: 30 new confirmed donor-to-company connections. Nothing here
  feeds the public site.

## Result (integrator, 28 October 13:45 NZDT)
Merged, gate green at the first run; the queue item deleted and the decision queue rebuilt at the merge. Released; `qv4-links-build` queued to carry the rule onto the live links and groups. Christopher & Banks Limited, two companies under one name with no year in brackets, is noted for Arthur as a candidate fifth rule (removal and registration months apart with a shared person: "succeeded by"). Branch and the working copy retired.
