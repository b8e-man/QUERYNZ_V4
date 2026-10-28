# fix-products-report-4: the report reads a name-only star through its centre, so a spoke reaches every namesake
branch: fix/products-report-1 (pushed; fdefe28, one commit on 64365a5)
session: fix-products-report-1 (fix, Opus, scope products/report/)
raised: 2026-10-29
found by: fix-products-templates-1 (blocker card `the-report-walk-reads-a-namesake-star-one-hop-so-a-spoke-sees-only-the-centre.md`, on its branch)
claims: products/report/ (walk.py, spec.md; tests/test_star.py and tests/test_star_real.py new);
lessons/a-star-drawn-near-rule-is-read-through-its-centre-never-one-hop-from-a-spoke.md, lessons/INDEX.md;
cards/charity-officers-are-in-no-link-and-no-name-row.md (a dated note); docs/status/report.md

## What it does

1. **The star.** The links lane stores `name-only@1` as a star (links/spec.md, the contract for readers, on
   `integrate/fix-links-5`). `walk.links_of` now calls `walk.star_links`. For each `name-only@1` link on the
   refs, it reads the other end's `name-only@1` links whose name key matches (`evidence.first_last`; an anchor
   row carries one name, so a link with no key belongs to its star).
   - Each namesake is reached once and is near, with the reason `NEAR_NAMESAKE`. That reason does not depend
     on which row is the centre.
   - The item's `path` holds [the subject's row, the centre, the namesake].
   - The read is capped at `LIMITS["star"]` = 400, and links past the cap are counted in `omitted`.
   - When the subject is the centre, nothing is added and nothing is listed twice.
   - Confirmed and related links are unchanged.
   - Because the change is in `links_of`, the officers' reach and a filed row's adopted group read stars the
     same way.
2. **The group.** `group_of` orders `row_key = group_id desc, row_key collate "C"`, so the group id is always
   among the 300 rows passed.

## Measured (read-only, live, 28–29 October)

- **Prohibition rows.** 160 Gazette prohibition rows carry a `name-only@1` link, and 159 of them are spokes.
  926 other components sit in their stars. Reached by the walk's link read from every other component:
  70 of 160 before, 160 of 160 after. Component-to-row misses fell from 765 to 0.
- **Walk time** from a spoke of each of the ten largest stars (448 to 1,531 links): 0.03–1.9 s before,
  1.0–4.1 s after. Near links went from 1 to 400, the cap; the rest are counted.

## Checks

- `tests/test_star.py`: 5 fixture tests.
  - A three-spoke star where the subject is a spoke finds both other spokes, once each, with their paths.
  - What a spoke sees is the same whichever of four rows is the centre.
  - The centre gains nothing twice.
  - The cap is counted.
  - The group id comes first.
  - Mutating back to one hop (`out["near"] += []`) turns 3 of the 5 red.
- `tests/test_star_real.py` (slow, live): a prohibition spoke is reached from up to ten other spokes of its
  star, and a spoke of the largest star lists more than one star namesake, each near, through the centre.
- `QV4_INTEGRATOR=1 bin/fast products/report`: green in 44.5 s.
- `pytest -m slow products/report`: green.
- `python -m products.report check`: 1 problem, which main has too (a director's charity officer by name).
  It comes from the walk's charity-officer bridge, which is older than ruling 114's links. Noted on
  `cards/charity-officers-are-in-no-link-and-no-name-row.md`; this change does not cause it.

## For the integrator (outside my fence)

1. **At this merge**, in `products/templates/08-recruitment/tests/test_recruitment_real.py`
   (branch `fix/products-templates-1`):
   - Remove the strict xfail marker on
     `test_the_most_shared_name_lists_its_namesakes_whichever_row_carries_the_star`. It XPASSes with this walk.
     The brief named `…keeps_its_namesakes_apart_and_never_confirmed`, but the marker is on this sibling.
   - Change line 104, `assert m["flags"]["bankruptcy"]["status"] == "blocked"`. The name's star holds three
     bankruptcy components, so the flag now fires amber ("…under a name near the subject's; a namesake's until
     confirmed"). Suggested: `assert m["flags"]["bankruptcy"]["status"] == "blocked" or (… == "fired" and
     m["flags"]["bankruptcy"]["severity"] == "amber")`.

   I ran the templates' whole slow suite in a scratch export of `fix/products-templates-1` with this
   `walk.py`. These two are the only changes.
2. Then run the templates' and the scan's slow tests.
3. Close the templates' blocker card.
4. **Restart `qv4-report` at the release.**

## Result (integrator, 29 October 05:16 NZDT)
Merged 01c7a81 as `integrate/fix-products-report-4`, gate green at the first run (the report's and the templates' slow tests; a first run was stopped by the integrator for a closed card lacking its date). At the merge the recruitment test's strict xfail was lifted and its bankruptcy assertion widened to the amber flag the star now reaches, as this request asked; the one-hop card closed. Released; `qv4-report` restarted. Branch and working copy retired.
