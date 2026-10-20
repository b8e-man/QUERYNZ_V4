# agriculture: where it stands

**Date:** 2026-10-20. **Step:** 5.2, template 2 (use case 4, agriculture
counterparty), `products/templates/04-agriculture/`. **Merge request:**
`agriculture-1` (raised).

## Done

- `template.toml`: 19 pub views with licence, attribution and refresh; seven
  sections in the credit manager's order (namesakes apart; officers and
  holders of record with dates; Gazette receiverships, liquidations,
  winding-up applications, administrations, creditors' notices, removals,
  bankruptcies, prohibitions; the people's other companies and their fate;
  charity and society roles; political money; what is not held); depth 1.
- `rules.py`: 19 flags for the old four company rules (register-status for
  partnership-dissolved; entity- and officer-group-insolvency for
  group-receivership; practitioner-repeat and mpi-coverage blocked) plus
  identity, removals, prohibition, bankruptcy, other-companies,
  officers-of-record, company-holders, hubs-met, young-entity, namesakes,
  charity checks, political money, replaced return. Every rule branches on
  the start kind; from a company the five people checks are blocked.
- Checkpoint on 12 real subjects: all print, none refused, 0.1 to 1.3 s;
  three facts read against the Gazette source file. `limits.md` written.
- Tests: 21 fast (fixtures, the shape's CLI), 4 slow (real tables).

## Carded

Report lane: `a-company-start-does-not-follow-its-officers`,
`insolvency-practitioners-are-not-reached-from-a-notice`,
`not-held-lacks-unincorporated-entities-and-mpi`. Links:
`a-companys-same-name-companies-are-not-set-apart`. Companies:
`a-company-holder-carries-no-business-number`.

## Next

1. The integrator merges `agriculture-1`; nothing to install.
2. When the report lane follows a company's officers, unblock the five
   people checks (a fix in this folder); when it exposes its contract
   (`report-2`), drop this template's own `flag`.
3. Step 5.2, template 3: use case 3, banking director history.
