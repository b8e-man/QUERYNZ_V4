# hdc-1: the Health and Disability Commissioner decisions lane (step 5.3, use case 11), built and held on terms
branch: session/hdc-1 (pushed; a2155b8)
session: hdc-1 (Opus)
raised: 2026-10-21
claims: registers/hdc_decisions/ (capture, read, load, check, tables, publish, sample, sample.list, pane, spec, README, profile-proposed.jsonl, position/, tests); docs/status/hdc-decisions.md; one queue item (no default); one card; one lesson

## What the lane is

- `pub.hdc_decisions`: one row per decision or case study the Commissioner lists from 2017 (ruling 71): file
  number, date, kind (the gravest finding stated, or 'case study'), findings per party, provider kinds, occupations
  and Code rights as the Commissioner tags them, rights stated as breached, recommendation headings and addressees,
  a named practitioner as a role plus the naming policy's ground, the page's address.
- `pub.hdc_decision_providers`: one row per provider organisation a page names, as named, with its findings, rights
  breached, whether a recommendation goes to it, and a company or charity number only where printed beside it.
- Never kept: the heading, any paragraph, a consumer, family member or letter label, age, condition, place beyond
  the provider, a practitioner's name, staff, a case study's address (its slug is its summary; private twin). Every
  kept text passes `read.consumer_detail`; the check runs it over both views.
- Proved on 12 real pages (2017 to 2026, both drafting forms, two case studies) in the sample database: 36 requests
  5 s apart. 35 fast tests, 16 mutants, a planted consumer detail refused by reader and check.
- Outside figure: the Commissioner's "Page 1 of N" per year, twelve a page; 168 pages in all (2,010 since 1998);
  2017: 5 pages, 49 decisions.

## Held

The Commissioner's copyright 3.1 allows research use only; 3.2 wants written permission for any other. Capture into
`querynz_v4`, `load --job`, `load.load` (staging) and `publish` refuse until `position/hdc-decisions.md` carries an
`authorised:` line. Queue: `docs/decisions/queue/whether-the-hdc-decisions-may-be-copied-for-the-estate.md` (no
default). Card: `the-hdc-lane-is-held-on-the-commissioners-copyright-terms`. check.py is red while held, correctly.

## For the integrator at the merge

1. Add `hdc_decisions` to `support/db` `LANES` (schema and its `_private` twin).
2. Move `registers/hdc_decisions/position/hdc-decisions.md` to `docs/legal/positions/`.
3. Append the four profiles in `profile-proposed.jsonl` to `support/profiles/profiles.jsonl`.
4. Regenerate the board (the new card makes it stale: `tests/test_generators.py` is red on this branch for that
   reason only), the lessons index and the queue.
5. No jobs to install while held; the two proposed jobs are in spec.md.

## Fast tier

Lane: green in 33 s. Whole repository: red on `tests/test_generators.py::test_the_committed_records_generate_cleanly`
only (the board, item 4); 420 s, target 300 s missed (recorded). The scratch schemas `scratch_hdc_1_proof` and
`scratch_hdc_1_proofread` in the sample database hold the proof; the safety hook kept me from dropping them.

Lesson: `a-health-complaint-page-s-heading-and-a-case-study-s-address-describe-the-consumer`.

## Result (integrator, 2026-10-21 22:53 NZDT)

Merged into main as 26a0c42 (`merge integrate/hdc-1: gate green`). Branch `integrate/hdc-1` from `session/hdc-1` (a2155b8), main merged. The lane is HELD on the Commissioner's copyright terms (3.1 research use only; 3.2 written permission for any other): queue item `whether-the-hdc-decisions-may-be-copied-for-the-estate` stands with no default, card `the-hdc-lane-is-held-on-the-commissioners-copyright-terms` open. Integrator items: `hdc_decisions` in the lane list with its schemas applied with grants on both databases; the position moved to `docs/legal/positions/hdc-decisions.md` (the queue item now names that path); the four profiles appended as version 1 (107 slugs); no job installed (the two proposed wait in spec.md); the lesson's first line cut to 240 characters. The overseas investment board views carried with it. The fast tier was first red: the lane's profile test read the proposed file this merge removes; it now reads the ledger for the four slugs. Fast tier then green in 488.8 s. Gate green; staging ran the held load: nothing read, nothing published. The drops of `scratch_hdc_1_proof` and `scratch_hdc_1_proofread` in the sample database are Arthur's. Arthur's too: the letter to the Commissioner the session recommends. Branches and the working copy retired.
