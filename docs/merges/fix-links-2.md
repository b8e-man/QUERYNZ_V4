# fix-links-2: `refiled-name@1`, ruling 109 ("delisted/refiled same year": 2 company pairs; Christopher & Banks is not one)
branch: fix/links-1 (pushed, e6b3241; one commit on main's 02586b6)
session: fix-links-1 (Opus, fix weight, scope links/)
raised: 2026-10-28
claims: links/ (rules.py, build.py, check.py, measure.py, pairs.py, spec.md, README.md, measurements.md, tests/test_rules.py, tests/test_links.py); docs/decisions/queue/ (one item new); one lesson, lessons/INDEX.md; docs/status/links.md
job after the merge: `qv4-links-build` (then `python -m links.check` live)

## The rule

`rules.refiled(a, b, shared)`, pure, beside `successor`. Two company rows
under one name key, neither carrying a year in brackets; ordered by
registration date (equal dates put the removed one first); the earlier was
removed, and the later was registered within twelve calendar months of
that removal, before or after it ("same year", either order). At least one
person confirmed on both, found as `successor-name@1` finds them (a
director or shareholder row on each, in one confirmed component; the lookup
is now `build.company_people` and `build.shared_people`, shared by the two
rules). Grade `related`, `relation` = "delisted/refiled same year"
(Arthur's words exactly), read earlier → later. Evidence as
`successor-name@1`'s (earlier, later, names, registered, removed, order,
shared_rows, shared_people) plus `removed_on`, `refiled_on` and `gap_days`
(negative where the new company was registered before the old was
removed). The name alone, or the name and the dates without a shared
person, stays near under `company-name@1`. A pair that relates leaves the
`company-name@1` near star. The groups walk confirmed links only: the slow
engine test now plants a refiled relation beside the succession, and it
fails when the walk is loosened to follow `related`.

## Measured first (live `links.*`, read login, 9 s)

| | pairs |
| --- | --- |
| companies under one name key, no year in brackets | 86,607 (65,592 keys) |
| of those, one of the two removed | 85,763 |
| removed and registered within twelve months | **12,607** |
| with a director or shareholder row on both companies | 7 |
| sharing a confirmed person (the rule's count) | **2** |

Built in `scratch_fix_links_2` (querynz_v4; `org_names`, `rows`, `groups`,
`decisions` and the company links copied from the live tables): **2
related**, matching the measurement. `company-name@1` near 87,891 → 87,889.
Groups do not change (a related link is never walked).

## Every related pair

1. CHATHAM ROCK PHOSPHATE LIMITED 1819800 (registered 2006-06-07, removed
   2026-07-31) → CHATHAM ROCK PHOSPHATE LIMITED 9446991 (registered
   2026-07-31); gap 0 days; 4 people on both.
2. PACIFIC HYGIENE LIMITED 564741 (registered 1992-11-10, removed
   2026-07-31) → PACIFIC HYGIENE LIMITED 9444168 (registered 2026-07-13);
   gap −18 days (registered before the removal); 3 people on both.

## Christopher & Banks is not related, and why

CHRISTOPHER & BANKS LIMITED 3482091 (registered 2011-07-28, removed
2024-12-18) and 9321019 (registered 2025-03-06) fit the name and the
dates (78 days apart), but 3482091 has no director or shareholder row in
`pub.directors` or `pub.shareholders`, so no person can be confirmed on
both. The published register keeps people for 3,360 of 1,099,638 removed
companies: only those a monthly file the companies lane holds still listed
(both related pairs were removed on 2026-07-31). `pub.company_lookup_roles`
is empty. The pair stays near. This is the register not seeing the people,
not a finding that none were shared. Queued for Arthur:
`docs/decisions/queue/a-refiled-company-whose-removed-half-has-no-people.md`
(recommendation: the companies lane fills the lookup roles for the removed
half of the 12,607 pairs; relating on name and dates alone is what ruling
109 refused).

## Checks and tests

- `check.py` item 6 now reads both relations: every related link is
  `successor-name@1` "succeeded by" or `refiled-name@1` "delisted/refiled
  same year" (it failed any other before), no group holds both rows, and
  every one still has a person in one group on both companies. Item 8, new,
  in SQL apart from the Python: every refiled relation is one name key with
  no year in brackets, the earlier removed, the later registered within
  twelve months of the removal, a shared person in the evidence. On the
  scratch: 953 related, 0 in one group; 2 refiled, 0 outside, 0 without a
  person. Planted in a rolled-back transaction, each turned 6 and 8 red: a
  refiled relation five years apart, one with no shared person.
- Measurement 9 (`measure.py`), the table above and the pair list, with
  `related_beyond_twelve_months` and `related_without_a_shared_person`,
  both 0. Written up as section 9 of `links/measurements.md`.
- Test pairs: two kinds, `companies-refiled-within-twelve-months` (7, every
  pair the registers supply) and `companies-one-name-beyond-twelve-months`
  (2), truth "two people" (two bodies); measurement 3 judges them with
  `rules.refiled` and the groups: 0 in one group, 2 related, 0 related
  beyond the twelve months or without a shared person. In `ORG_KINDS`, so
  the review agent does not score them.
- Unit tests on the real dates (Christopher & Banks, given a shared person,
  relates with gap 78; Pacific Hygiene −18), the twelve-month edges (29
  February + 12 months = 28 February), no person, neither removed, the
  later one removed, a year in brackets, an unknown date.
- `QV4_INTEGRATOR=1 bin/fast links`: green (47 s). `links/tests` with the
  slow tests: all pass.

## The board and the report (read only; nothing changed there)

A second relation value prints with no change: the board's pane
(`products/board/panes.py:1128-1130`) and lineage frame label
(`products/board/lineage.py:57-59`, `label` at 180) and the report's
related line (`products/report/walk.py:571-586`, "{earlier} {relation}
{later}") all read `pub.links.relation`. Neither hard-codes "succeeded by"
in a printed relation. Prose still written for ruling 106 (2) only, for the
integrator to carry:

1. `products/board/panes.py:1106-1108` `RELATED_NOTE`: "companies under one
   name, one carrying a year in brackets".
2. `products/board/lineage.py:42-44` `WORDS` (the graph's note): the same.
3. `products/board/catalogue.py:111-129` `RULE_WORDS` has no
   `refiled-name`, so the pane reads "links rule refiled-name" (the
   fallback; nothing hidden). Suggested: "a company removed and another of
   its name registered within twelve months, a person on both".
4. `products/report/build.py:24-27` `RELATED_SECTION`: heading "Related
   companies: one succeeded by another", text "one with a year in
   brackets".
5. `products/report/catalogue.py:279-288` `RULE_WORDS` has no
   `refiled-name`, so the memo prints the raw id `refiled-name@1`.

## After the merge

Run `qv4-links-build`, then `python -m links.check` live (items 6 and 8).
`scratch_fix_links_2` is Arthur's to drop with the earlier scratch
schemas. Nothing in this request reads or prints a home address or a
suppressed name; the pairs above are company names and numbers.

## Result (integrator, 28 October 17:19 NZDT)
Merged 4d6ce9f, gate green at the first run. At the merge the report's related texts were reworded to cover both relations (products/report build.py RELATED_SECTION, catalogue.py RULE_WORDS gains refiled-name); the board's three texts go to board-12's brief, the board being held by board-11. Released; `qv4-report` restarted; `qv4-links-build` queued 17:19 (row 678). The queue item `a-refiled-company-whose-removed-half-has-no-people` stands for Arthur: the rule relates 2 pairs today because the published register keeps people for 3,360 of 1,099,638 removed companies. Branch and the working copy retired.
