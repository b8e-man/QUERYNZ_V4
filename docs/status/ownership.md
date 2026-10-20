# ownership: where it stands

**Date:** 2026-10-21. **Step:** 5.2, template 13 (beneficial ownership and
AML checks, domestic half), `products/templates/13-ownership/`.
**Merge request:** `ownership-1` (raised).

## Done

- `template.toml`: 19 pub views with licences; six sections (namesakes;
  holders of record and the chain as far as it reaches, one hop; directors
  and office; Gazette; public office and political money; not held).
- `rules.py`: 19 flags; sanctions, for-whom-held and holder hubs never clear;
  `CHAIN_DEPTH = 4`, `CHAIN_REACHED = 1`.
- Tests: fixtures, 15 mutants all caught (fast); two real-table tests (slow).
- Checkpoint on twelve real subjects (`checkpoint.list`), none refused; four
  rule faults found and fixed there; `limits.md` written.

## Carded

- `the-walk-does-not-follow-a-company-holder-up-the-chain` (report, companies)
- `the-shareholders-view-carries-no-parcel-or-issued-shares` (companies)
- `a-holders-count-of-companies-is-not-read-for-a-hub-flag` (report)
- `the-catalogue-names-no-overseas-registers-or-trusts-as-not-held` (report)
- `node2-lost-its-wired-link-and-an-orphaned-links-load-holds-its-locks` (blocker)

## Next

1. Re-run the checkpoint once the links are reloaded (it ran on 2,614,679).
2. When a holder carries a key and the walk follows it, raise `CHAIN_REACHED`
   and turn `holding-chain` into the hop list (a fix in this folder).
3. The sanctions lists, when a lane publishes them, turn `sanctions-lists`
   into a real screen.
