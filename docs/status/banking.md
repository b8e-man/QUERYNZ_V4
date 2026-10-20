# banking: where it stands

**Date:** 2026-10-20. **Step:** 5.2, template 3 (use case 3, banking
director history), `products/templates/03-banking/`. **Merge request:**
`banking-1` (raised).

## Done

- `template.toml`: 19 pub views with licence, attribution and refresh;
  depth 2; seven sections in the analyst's order (namesakes apart; roles and
  holdings with dates; how each company ended, status and Gazette notices
  beneath it; prohibitions and bankruptcies; the people beside; charity,
  society and political money; not held, the securities register named).
- `rules.py`: 20 flags on the bound contract (company-endings,
  insolvency-notices, repeat-insolvency, left-before-notice,
  register-removals, past-roles, prohibition, bankruptcy, young-entity,
  namesake-exposure, shared-boards, walk-coverage, subject-hub,
  officers-of-record, company-holders, charity ×2, political-money, comcom,
  securities). Every rule branches on the start; from a company the people
  checks block. `HISTORY = False`: the companies file holds current roles
  only, so no check over a person's companies clears.
- Checkpoint on 12 real subjects (`checkpoint.list`): all print, none
  refused, 0.3 to 8.4 s; three facts read against the Gazette source file.
  `limits.md` written.
- Tests: 32 fast (fixtures; a mutant check, ten mutants each caught), 3 slow.
  `bin/fast products/templates` green 27.5 s; `python -m products.report
  check` green; one-way test green.

## Carded

Companies lane: `the-companies-file-holds-no-past-directorships`. Report
lane: `the-walk-reads-twelve-companies-and-lists-forty`,
`a-contested-groups-near-row-can-make-the-start-rows-own-company-near`,
`a-crown-entity-holder-is-not-flagged-as-the-crown`,
`group-standing-calls-a-filed-row-with-no-group-an-organisation`,
`a-section-cannot-put-current-roles-first`.

## Next

1. The integrator merges `banking-1`; nothing to install (`qv4-report`
   serves every template on disk).
2. When a view publishes past roles with end dates: `HISTORY = True` (a fix
   here). When the walk follows a company's officers, unblock the people
   checks from a company start.
3. Step 5.2, template 4: use case 2, legal counterparty.
