# scan: where it stands

**Date:** 2026-10-28. **Step:** 6.1, the register-scan shape, `products/scan/`.
**Merge request:** `scan-1` (raised). **Port:** 8450 (beside the report's 8440).

## Done

- The shape: a scan template (`templates/<name>/template.toml`: the
  question, the views with licences, the join as steps by row, by person
  through the links, or by a link rule, the columns carried, the limits);
  one runner (`run.py`) compiling the steps to one query over `pub`,
  streaming it in pages, grading each line (confirmed, near, contested)
  under the two trust settings (`settings.toml`, both "default in force";
  the queue's two items stand), numbering citations once per row as the
  report does, flagging hubs, recording every view's `loaded_at` and the
  time; the stale rule (`stale`, `run --stale`); the list as a paged page
  (`serve`, 200 a page, filtered by grade, citations beneath) and as
  `answers.csv`, `answers.json`, `citations.csv`; the presentation rules
  (`rules.py`) refusing a run; the check (`check.py`, green, 1.5 s); the
  unit `qv4-scan`; the proposed job `qv4-scan-rerun` (`jobs-proposed.toml`).
- Proved on the real tables (this session's scratch schema):
  `society-officers-liquidations` 854 lines in 1.4 s (97 confirmed, 757
  contested: two professional directors' groups the watch flagged make
  672 of them, each line flagged as a hub); `donors-named-as-companies`
  287 lines in 1.2 s (177 from party returns, 110 from disclosures, all
  near by the rule, cited). A join over the whole companies register
  (every company with a liquidation notice, a timing run only): 59,786
  lines in 5.8 s, a page served in 0.15 s, the file streamed in 1.1 s.
  The stale rule fired for real when the links rebuilt at 15:22 and the
  re-run brought both back to current. Under the other chains setting
  (direct links, not in force) the society scan takes about two minutes.
- Fast tier 22 tests (fixtures; the mutant check plants ten faults and the
  rules catch each); slow tests 9 s; one-way and reading-limit tests green.
- fix-products-scan-1 (29 Oct): a name-only@1 link is read between the two
  rows' groups (links contract for readers), every other rule between the
  rows; procurement templates 1.1. 30 stored lines stay red until a re-run:
  queue `two-groups-away-from-a-name-star-s-centre`.

## Carded

- Links: `a-person-step-cannot-reach-a-filed-row-through-the-groups`,
  `the-organisation-name-rule-reaches-past-the-exact-filed-name`,
  `charity-officers-and-organisation-rows-are-not-in-the-names-table`.
- Integrator: `the-scan-rerun-job-into-the-catalogue` (state tables, first
  runs, the unit, the job). Idea: `a-shared-catalogue-of-the-published-views`.

## Next

1. The integrator merges `scan-1` and works the blocker card.
2. Step 6.2's templates, in the plan's order, on this shape; the first
   (tender awards) needs its lane first.
