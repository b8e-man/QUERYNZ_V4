# fix-products-scan-1: the scan reads a name-only@1 link between the two rows' groups
branch: fix/products-scan-1 (pushed, 72fe3d1; one commit on main's e9930c7)
session: fix-products-scan-1 (Opus, fix weight, scope products/scan/)
raised: 2026-10-29
claims: products/scan/ (check.py, plan.py, the two procurement templates (now 1.1), templates/_tests/test_scan_templates.py, tests/test_name_step.py, tests/test_template_and_plan.py, tests/test_templates_real.py); docs/decisions/queue/two-groups-away-from-a-name-star-s-centre.md (new); one lesson, lessons/INDEX.md; docs/status/scan.md
depends on: integrate/fix-links-5 for the contract's wording in links/spec.md; the code reads only pub.links and pub.groups and runs on main as it is
job after the merge: queue `qv4-scan-rerun` for procurement-directors-donors and procurement-shareholders-donors. Their stored runs, 154 and 155, are what stays red (below).

## What the scan now asks the links lane

- **`check.link_between(pub, rules, a, b)`** is the one pair lookup, used for
  the organisation scan (check.py, former line 198) and the procurement scans
  (former line 278). A star rule, `plan.STARS = ("name-only@1",)`, is looked
  for between the two rows' groups in pub.groups, with a row in no group as
  its own. The link may sit on any row of each group, so neither the group id
  nor the old centre is assumed. Every other rule is looked for between the
  two rows. Stored lines keep their row refs, and the groups are worked out
  at check time.
- **`plan.reached`** replaces the old join for a link step (`by = "link"`).
  A star rule's link is read from every row of this row's group and lands on
  every row of the other end's group. Every other rule's link is read from
  the row itself. The line's grade, reason and rule come from the link found,
  so a near line's reason is the reason on the link between the two groups.
  The person step under "direct" is unchanged.
- **Why only name-only@1.** First I applied group reading to every rule.
  Director lines went from 80 to 7,586, because every confirmed directorship
  in a donor's group came along. The organisation lines went from 45 to 117.
  The contract names name-only@1 only, and the brief keeps confirmed links
  by rows.
- **Speed.** A flat join to pub.links on a group member made the planner hash
  all four million links and join them to the groups twice, which ran past
  the ten-minute limit. The lookup is now a lateral `offset 0` by one row's
  key: 12 to 18 s a start on live (the old query took about 46 s for the
  three starts).

## The eleven lines, and what stays red

Live, read-only, every stored line read back one at a time (no names in this
request; the lines are numbered in their runs):

| Run | Stored | Green again | Still red | Why red |
| --- | --- | --- | --- | --- |
| procurement-directors-donors 154 | 80 | 51 | 29 | 28 two leaves of one name-only star; 1 a confirmed pair in one group whose full-name star moved off both rows |
| procurement-shareholders-donors 155 | 6 | 5 | 1 | a confirmed pair in one group whose full-name star moved |

**None of the eleven lines is found again. In each case the near link really
is gone** (director lines 1 to 11, all among the 28). In each, the donor row
and the director row are both in no group, and pub.links holds no
name-only@1 link between them or their groups. Both sit as leaves of a star
whose centre is now a third row. Red director lines: 1 to 12 and 17 to 33.
Red shareholder line: 1. The line found only between the two groups is green
again.

The lane draws a star from one centre, not "one link per pair of
components" as its contract says, so no reader can find two leaves. That is
the queue item, with no default for the lane: it either draws one link per
pair or says how a reader finds a leaf pair. `full-name@1` is a star too, and
that explains the two confirmed lines.

The new walk on today's links: 142 director lines and 139 shareholder lines.
Every line the old walk gives today is among them (old 50 and 5, none
missing). Built in memory and read back line by line, they show 0 problems
and 0 presentation-rule problems, and the planted person is caught on both.
`donors-named-as-companies`: 45 lines, the same 45 as the old walk.

## Tests

- `QV4_INTEGRATOR=1 bin/fast products/scan`: green, 42.8 s.
- Scan slow tests on live: 12 passed, 1 skipped, 2 failed.
  - `test_the_procurement_read_back_holds_and_catches_a_planted_person` is
    red on stored runs 154 and 155, for the 30 lines above. It goes green
    once `qv4-scan-rerun` has run, because the new walk's lines all read
    back green.
  - `test_real.py::test_the_two_proving_scans_run…` fails because the owner
    login on live is refused to a session (`LiveRefused`). It writes a run,
    so this has nothing to do with the change.
  - The rest of `tests/test_templates_real.py` is green.
- New: `test_a_near_link_between_two_group_ids_is_found_from_two_other_rows_and_the_row_lookup_would_miss_it`.
  It uses a live name-only@1 link whose two ends are both group ids, read
  from a director row of each group that is neither end. The check finds it,
  and the walk reaches the other row with the link's own reason. Inside the
  test, the row-lookup form finds nothing. Mutations run and restored: the
  row lookup in plan.py (MEMBERS and GROUP_ROWS) and `STARS` emptied each
  turn it red.

## Result (integrator, 29 October 05:00 NZDT)
Merged 12e90f4 as `integrate/fix-products-scan-1`, gate green at the first run (the scan's slow tests). The stale scans were re-run by hand from this branch against live on 29 October 00:05 to 03:45 (every stale scan, the procurement pair as runs 403 and 404, version 1.1), so the read-back test was green at the gate. Released. The decision-queue item `two-groups-away-from-a-name-star-s-centre` stands for Arthur, alongside his 29 October observation that near links are an entity relation and belong between group ids. Branch and working copy retired.
