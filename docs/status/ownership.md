# ownership: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 13 (beneficial ownership and
AML checks, domestic half), `products/templates/13-ownership/`.
**Merge request:** `ownership-1` (not yet raised).

## Done

- `template.toml`: 19 pub views with licences; six sections (namesakes;
  holders of record and the chain as far as it reaches; directors and
  office; Gazette; public office and political money; not held).
- `rules.py`: 19 flags; sanctions, for-whom-held and holder hubs never clear.
- `tests/test_ownership_template.py`: fixtures, 12 mutants, all caught.

## Half-done

- Checkpoint on twelve real subjects: blocked at 07:50 by node2's wired
  link going down (both NICs no carrier; 10.0.0.10 and 10.0.0.2 gone),
  which hung the integrator's links reload holding the locks on
  `links.decisions`; every `pub.links` read waits.

## Carded

- `the-walk-does-not-follow-a-company-holder-up-the-chain` (report, companies)
- `the-shareholders-view-carries-no-parcel-or-issued-shares` (companies)
- `a-holders-count-of-companies-is-not-read-for-a-hub-flag` (report)
- `the-catalogue-names-no-overseas-registers-or-trusts-as-not-held` (report)

## Next

Run the checkpoint, write `limits.md` and `checkpoint.list`, push, raise.
