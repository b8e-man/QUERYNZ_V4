# construction: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 6 (use case 7, subcontractor
vetting and phoenix detection), `products/templates/07-construction/`.
**Merge request:** `construction-1` (raised).

## Done

- `template.toml`: 12 pub views with licence, attribution and refresh;
  depth 2; eight sections in a procurement lead's order (namesakes apart;
  officers and holders, dated; the phoenix section, every company reached
  with status and start; registered offices; prohibitions and bankruptcies;
  the people beside and society roles; the Gazette on the entity and the
  companies above; not held, five registers named).
- `rules.py`: 26 flags on the bound contract. `phoenix-signature`: a failure
  dated from its Gazette notice beside a going company's start, window 365
  days either side (`WINDOW_DAYS`, a setting), raised only on a shared
  person or a pre-failure shared office, never a name; hub, near or removal
  never red. `same-name-failed` info/amber. From a company the people checks
  block. `HISTORY = False`.
- Checkpoint on 12 real subjects: 11 print, 1 refused by the shape (a
  company named like an address, carded), none broke a rule, 0.3 to 6.0 s;
  three phoenix cases in construction trades raised red (4, 7, 34 days);
  three facts read against the Gazette source file. `limits.md` written.
- Tests: 32 fast (fixtures; a mutant check, fourteen mutants each caught),
  4 slow (real tables). `bin/fast products/templates` green 28.3 s; one-way
  and reading-limit tests green. `python -m products.report check` has one
  problem not of this branch (carded:
  `confirmed-expense-links-put-every-category-line-in-a-members-report`).

## Carded

Report lane: `a-company-named-like-a-street-address-refuses-every-report-that-meets-it`,
`the-walk-counts-the-companies-at-an-office-and-does-not-list-them`,
`a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`,
`the-not-held-list-lacks-employment-determinations-and-the-change-history`,
`confirmed-expense-links-put-every-category-line-in-a-members-report`.
Companies lane: `a-liquidated-companys-office-before-its-liquidation-is-not-published`.
Templates 2, 3, 4, 13: `four-templates-still-say-no-link-reaches-a-bankruptcy`.
Leans on the open `a-company-start-does-not-follow-its-officers`.

## Next

1. The integrator merges `construction-1`; nothing to install (`qv4-report`
   serves every template on disk).
2. When the walk follows a company's officers: unblock the person half of
   the signature from a company start (a fix here). When the walk lists an
   office's companies, or past offices are published: the office half.
3. Arthur: the window (365 days either side) is a default; say if another.
