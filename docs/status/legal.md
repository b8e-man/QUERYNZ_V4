# legal: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 4 (use case 2, legal
counterparty and conflict check), `products/templates/02-legal/`.
**Merge request:** `legal-1` (raised).

## Done

- `template.toml`: 20 pub views with licence, attribution and refresh;
  depth 2; six sections in a conflicts clerk's order (namesakes apart;
  officers and holders of record with dates; the conflict web, each company
  the person sits on with the people on it, near; the Gazette on the company
  and its people; charity, society and political money; not held, court
  judgments and disciplinary findings named).
- `rules.py`: 27 flags on the bound contract, standing for MC-L1 to MC-L5
  and the old person and company rules: client-overlap (always blocked:
  the firm's list is not an input), conflict-web, shared-boards,
  officers-of-record, holders-of-record, shared-office, company-status,
  insolvency-notices (a deed of company arrangement counts), repeat-
  insolvency, amalgamation, register-events, mortgagee-possession,
  prohibition, bankruptcy, practitioner-roles, young-entity,
  namesake-exposure, walk-coverage, subject-hub, past-roles, the charity
  and money checks, court-judgments, disciplinary-findings, comcom,
  securities. From a company the people checks block; a donation that
  takes a person's group is read as that person. `HISTORY = False`.
- Checkpoint on 12 real subjects (`checkpoint.list`): all print, none
  refused, 0.3 to 6.1 s; three facts read against the Gazette source file.
  `limits.md` written.
- Tests: 36 fast (fixtures; a mutant check, twelve mutants each caught), 3
  slow (real tables). `bin/fast products/templates` green 28.2 s;
  `python -m products.report check` green; one-way test green.

## Carded

Report lane: `a-template-cannot-take-the-firms-client-list`,
`the-catalogue-does-not-know-gazette-possessions`,
`the-not-held-list-lacks-disciplinary-findings-and-tribunals`,
`an-amalgamation-notices-other-companies-are-not-reached`,
`a-liquidator-row-does-not-name-its-company`. Gazette lane:
`an-amalgamation-row-carries-no-effective-date`. Leans on the open
`a-company-start-does-not-follow-its-officers`.

## Next

1. The integrator merges `legal-1`; nothing to install (`qv4-report`
   serves every template on disk). The root suite rewrites `docs/board.md`
   and `lessons/INDEX.md` in the working copy; left unstaged (generated).
2. When the report takes a client list: `client-overlap` fires or blocks
   (a fix here). When the walk follows a company's officers: unblock the
   people checks from a company start. When step 5.4 publishes judgments:
   a courts section and `court-judgments` reads it.
