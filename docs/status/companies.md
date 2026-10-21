# companies: where it stands

**Date:** 2026-10-21. **Step:** 4.1 merged (`companies-1`); 5.5 company
monitoring built, `registers/companies/monitor.py`. **Merge request:** `companies-2`.

## Done

- Monthly lane: 1.92 M entities, unchanged (`docs/merges/companies-1.md`).
- Monitor: products ask through `pub.request_company_check` /
  `pub.watch_company` (owner-rights functions, product reader only, asker =
  login); one gated call per entity, 5 s apart, at most 300 a NZ day, nothing
  fetched twice a day; answers landed by hash; dated changes with citations
  in `pub.company_changes`; roles with the register's own end dates.
- Proved on 8 real entities, 21 October 11:05 NZDT, all 200, no challenge:
  5 sample companies (one real change: in liquidation in August, removed
  now; 0 false), a sole trader (name withheld by the register), a
  partnership, a trading trust. The real lane gives the same one change.
- Tests: 25 new (fast on invented answers and the sample; one slow).

## The interface, under the four questions (ruling 61; read 21 October 2026)

1. **Open?** Yes, with our own free subscription key; no lock got past.
2. **Lawful copying?** The register is public by statute (NZBN Act 2016,
   Companies Act 1993). The portal names no licence ("There is no fee for
   using this API"; "MBIE is not liable for the accuracy"). Copying register
   contents is the lawyer's question (card `the-nzbn-api-terms-and-the-copying-of-register-contents`).
3. **Terms accepted?** The portal's at registration; no rate limit stated
   anywhere read (portal page, nzbn.govt.nz terms of use). Asked: keep batch
   jobs off Wednesday 21:00–23:00; use `ETag`. Ours: 300 calls a day, 5 s apart.
4. **Privacy and statute?** Directors' and shareholders' addresses are
   persons' and go to `companies_private` only; so does every address of a
   sole trader, partnership or trust; e-mail and phone are never read.
   Only a company's or society's registered office is shown (hard limit 15).

## Carded

- `the-companies-monitor-job-into-the-catalogue` (blocker, integrator).
- `the-nzbn-interface-has-a-change-search-and-watchlists` (Arthur).

## Next

1. The integrator's merge: job, profile, the position widened.
2. A product (the board, template 5) calls `pub.request_company_check`.
3. The old estate's August package holds 228,000 sole traders, partnerships
   and trading trusts (`bulk.unincorporated_entities_core_data`): the queue's
   default (not taken) stands; the monitor takes them one at a time.
