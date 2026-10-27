# links-3: three links rules from ruling 106
branch: session/links-3 (pushed; cb25bb1)
session: links-3 (build, scope links/)
raised: 2026-10-28
claims: links/rules.py, build.py, check.py, measure.py, tables.sql, publish.sql, __init__.py, spec.md, README.md, measurements.md, tests; docs/status/links.md; docs/decisions/queue/ (one item answered, one new); one lesson, lessons/INDEX.md

Each rule is a pure function in `links/rules.py` (`sole_company`, `successor`,
`same_party_candidates`). `build.py` reads the facts, calls the function and
stores what it returns. Built in `scratch_links_3` on the real published
tables: the rows gathered once, built with the old code (before), then with
the new code over the same rows (after), the live decisions copied in.

| | groups | rows in groups | contested |
| --- | --- | --- | --- |
| before | 681,628 | 2,315,125 | 52,085 |
| after | 681,815 | 2,315,735 | 52,085 |

## 1. `organisation-sole-company@1`, confirmed

A donation row (party returns, candidate returns, declarations) and the
one company on the register under its name key, live in the donation's year
(registered by the year's end, not removed before its start; a dated
declaration is a year of one day). Evidence: company number, the donation's
date and year, the company's registered and removed dates.
315 donation rows have a company of their name: **262 confirmed**. Near
under `organisation-name@1`, the reason says which: 70 pairs (30 rows)
several companies, 20 removed before the year, 3 registered after it.
The brief's 2,454 "one company" pairs held 2,195 declared interests
(`mp_interests`). Those are not donations; they stay near, unchanged.
Groups: the 418 rows (262 donations, 156 companies) were 178 rows in 87
groups and are now in 156 groups; 0 contested before or after.
Measured gap, queued (`one-company-of-several-live-in-the-donation-s-year`):
each of the 30 "several" rows has exactly one company live in the year.

Sample of 20 (donor as filed → company, number, year from, registered):
JBSR Limited → JBSR LIMITED 7679857, 2022, 2019-08-26 · Diemarco Projects
Limited 6832101, 2025, 2018-05-14 · 22 E.A.W Limited 9294221, 2025,
2024-11-11 · Go Bloodstock New Zealand Limited 2230396, 2017-09-21,
2009-05-20 · Luxury Infinity Investment Group Limited 4692482, 2025 · J Swap
Contractors Limited 178106, 2023 · RCL Henley Downs Ltd 4588159, 2018 ·
Shaw's Wire Ropes Limited 1045874, 2026-04-08 · COSGROVE & PARTNERS LTD
6465153, 2024 · Stark Property Limited 4793620, 2023 · Bathurst Resources
Limited 4382538, 2025 · Prostone Consulting Limited 5699868, 2025 · Harbour 5
Limited 2111678, 2014-09-18 · Porter Group → PORTER GROUP LIMITED 107335,
2017 · Williams Corporation Limited 5472041, 2026-05-21 · Atlas Concrete
Limited 554905, 2025 · Atom Data NZ Limited 9249560, 2026-09-07 · Alpha
Laboratories (NZ) Limited 945421, 2017 · Bayley Corporation Limited 342183,
2022-11-17 · Donald Properties Group Limited 7874214, 2023.
Worth a look on the board: "Porter Group" filed with no legal ending keys
to PORTER GROUP LIMITED. "NZ National Party" on 2023 candidate returns keys
to NEW ZEALAND NATIONAL PARTY LIMITED, removed in 2020, so it stays near.

## 2. `successor-name@1`, a third grade: `related`

The decision on how `pub.links` carries a relation: **`grade = 'related'`
and a new column `relation` = "succeeded by"**. A related link is two
entities and what the one is to the other, never an identity. The evidence
reads in date order: `evidence.earlier` is succeeded by `evidence.later`
(by registration date; 3 pairs with equal dates are ordered by key, and
`evidence.order` says so). `evidence.shared_rows` holds the people confirmed
on both, as pairs of row keys with their group id; `shared_people` counts
them. `tables.sql` widens the grade check in place, once, only where it
still lacks `related`, and checks that `relation` is present exactly when
the grade is `related`. `publish.sql` appends `relation` to `pub.links`. A
`contested` decision shows the pair as near; `not the same` agrees with it.
The groups walk confirmed links only. Proof: a slow test on the real engine
(fails when the walk is loosened), and a `check.py` check on the live tables.

Measured first, as asked, over `links.rows` and `links.groups` by key (18 s):
928 of the 13,635 stored near pairs share a confirmed person. The rule
judges every pair the name pattern makes, 17,366 (the near rule stores a
star, and a relation does not chain; that is the lesson filed):
**951 related**, 2,935 shared people, 639 pairs share more than one. The
928 leave `company-name@1`, and 12,707 stay near. In 86 pairs the company
carrying the year was registered first: it was renamed when the new
company took the plain name, and the date order handles that. Groups: no
group holds both companies of any pair. 1,427 company rows: 2 were in a
group before, 3 after (the third through rule 1).
For Arthur to read: many pairs are trustee companies of law firms
("BBW TRUSTEES (2006) LIMITED"), sister companies of the same partners
rather than a business that moved.

Sample of 20 (earlier, registered → later, registered; shared people):
PF TRUST SERVICES LIMITED 2003 → (2026) 2026, 5 · ANDERSON LLOYD TRUSTEE
COMPANY 1987 → (2013) 2013, 10 · THE CABIN SPECIALIST 2019 → (2022), 2 ·
SOUTHEND FARMS 1995 → (2025), 2 · WALKER DAVEY TRUSTEE SERVICES 2001 →
(2010), 7 · SCOPE CONSTRUCTION (2012) 2006 → SCOPE CONSTRUCTION 2012, 1 ·
SAFARI CONSTRUCTION (2015) 2014 → SAFARI CONSTRUCTION 2016, 1 · C & T
FREIGHT 2011 → (2015), 2 · PARNELL APARTMENTS 2006 → (2013), 2 · ICY
INDULGENCE 2026-03 → (2026) 2026-06, 1 · OTAGO VEHICLE BUYERS 2016 → (2025),
1 · NEILSONS TRUSTEE 2010 → (2020), 4 · WOODHOUSE KINSALE TRUSTEES 2008 →
(2016), 1 · DAVENPORTS HARBOUR TRUSTEE 2005 → (2011), 2 · SELLAR BONE
TRUSTEES 2000 → (2011), 3 · BUTLER GRAY TRUSTEES 2005 → (2009), 1 · MICHAEL
G STUART TRUSTEE CO 1996 → (1999) 1997, 4 · BBW TRUSTEES 1997 → (2006), 6 ·
VULCAN TRUSTEE CO 2005 → (2020) 2019, 7 · SAFARI TREASURY 2008 → (2019), 1
(all LIMITED).

**For the board (board-8 or later; not touched here):** draw a `related`
link as a frame around the two companies in date order (`evidence.earlier`
then `evidence.later`), labelled with `relation`. Draw the people in
`evidence.shared_rows` once, inside the frame. Never merge the two into one
entity node: they are two `pub.groups` entities, or lone rows. Today
`products/board/links_view.py`, `products/report/walk.py` and `graph.py`
treat any grade other than confirmed or near as near. So a related link
shows as near until the board draws it, and is never shown as confirmed.
The installer and `support/db` need nothing.

## 3. `candidate-same-party@1`, confirmed

House candidate rows under one name key and one registered party in
different elections are one person (a star from the smallest ref). Evidence:
party, the two elections, the seats (electorate, list place), the two
printings. Where two rows of the name stand for the party in one election,
no pair of that name and party confirms; they are near, and the reason
names the elections. Today: 206 names, **282 confirmed**, 0 refused (no name
stands twice for one party in one election). Unregistered party labels are
not judged. `candidate-name-form@1` 402 → 180: candidate pairs under one
printing are this rule's now. It keeps 143 same-printing pairs that touch a
member's seat and 37 different printings. Groups: 488 candidate rows, 118
in 88 groups before (seat to candidacy), 206 groups after; 3 contested
before and after. Test pairs redrawn: `two-candidates-one-election` 0 of 1
joined (two people), `member-and-candidacy` 144 of 144 joined (one person).

Sample of 20 (as printed, party, election and seat → election and seat):
LEWIS, Steph, Labour, 2020 Whanganui → 2023 Whanganui · WATTS, Simon,
National, 2020 North Shore → 2026 North Shore, list 13 · O'CONNOR, Damien,
Labour, 2020 West Coast-Tasman → 2026 Waitaki, list 16 · BELICH, Camilla,
Labour, 2020 → 2023 Epsom · UTIKERE, Tangi, Labour, 2020 → 2026 Palmerston
North · McANULTY, Kieran, Labour, 2020 → 2023 Wairarapa · CHHOUR, Karen,
ACT, 2020 Upper Harbour → 2026 North Shore, list 5 · TANGAERE-MANUEL,
Cushla, Labour, 2023 → 2026 Ikaroa-Rāwhiti · WAITITI, Rawiri, Te Pāti Māori,
2020 → 2026 Waiariki · GOLDSMITH, Paul, National, 2020 → 2026 Epsom ·
LAMBERT, Paula, Legalise Cannabis, 2020 → 2023 Christchurch East ·
GHAHRAMAN, Golriz, Green, 2020 Mt Roskill → 2023 Kelston · MACLEOD, David,
National, 2023 → 2026 New Plymouth · WALKER, Jordan, Green, 2023 East Coast
→ 2026 East Cape · TIRIKATENE, Rino, Labour, 2020 → 2023 Te Tai Tonga ·
MAHUTA, Nanaia, Labour, 2020 → 2023 Hauraki-Waikato · TOKO, Jamie, Labour,
2023 → 2026 Waikato · MEAGER, James, National, 2023 → 2026 Rangitata ·
LORCK, Anna, Labour, 2020 → 2023 Tukituki · ABEL, Steve, Green, 2020 → 2023
New Lynn. The House's 2020 and 2023 rows print no list place.

## Checks and tests

`check.py` on `scratch_links_3` (`--pub scratch_links_3_pub`): 33 of 33
green, four new (item 6): every sole-company link is a donation row and the
only company of its name, live in the year (an SQL count apart from the
Python); no candidate-same-party pair confirms a name that stands twice in
one election; no group holds both rows of a related link; every succession
still has a shared person in one group. In one transaction, rolled back, a
planted fault made three of them fail. The candidate check reads
`pub.candidates`, which a session cannot plant into, so its failure path is
proved only by the unit test. Measurement 7 added (`measure.py`,
`measurements.md`). Fast tier, links (`QV4_INTEGRATOR=1 bin/fast links`):
green in 41.8 s. Slow tests in `test_links.py` green.

## For the integrator

- After the merge, run **`qv4-links-build`**. `tables.sql` adds
  `links.links.relation` and widens the grade check in place. `publish.sql`
  appends `pub.links.relation`. Then run `check.py` live.
- Installer: nothing. `support/db`: nothing.
- Drop `scratch_links_3` and `scratch_links_3_pub` in querynz_v4, on
  Arthur's word. A `scratch_links_3` schema made by the sample fill is also
  in querynz_v4_sample.
- Queue: `may-a-company-name-alone-confirm-a-donor` is answered by ruling
  106 (1) (line appended). New item:
  `one-company-of-several-live-in-the-donation-s-year`.
- Lesson: `a-star-of-stored-links-is-not-every-pair-so-judge-a-relation-on-the-pairs`
  (index regenerated). No new card.
- Hard limit 14: rule 3 confirms new connections between candidacies of
  named people. Nothing here feeds the public site; it stays so until
  Arthur decides.

## Result (integrator, 28 October 12:20 NZDT)
Merged fc918b8, gate green at the first run; the lessons index and the decision queue rebuilt at the merge (`may-a-company-name-alone-confirm-a-donor` closed by ruling 106; `one-company-of-several-live-in-the-donation-s-year` raised, then answered by ruling 107 the same day: a links fix builds it). Released; `qv4-links-build` queued 12:20 to rebuild the live links and groups with the three rules (the table gains `relation`, the grade check widens, `pub.links` gains the column). The board shows a related link as near until a board session draws the lineage frame. The scratch schemas are Arthur's to drop. Branch and the working copy retired.
