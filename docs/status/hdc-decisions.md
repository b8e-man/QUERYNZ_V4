# hdc-decisions: where the lane stands

Session hdc-1 (Opus), 21 October 2026, node2. Step 5.3, the Health and
Disability Commissioner's decisions for use case 11, `registers/hdc_decisions/`.
**Built and held.** Merge request `hdc-1`.

## The four questions (hard limit 4)

1. **Open?** Yes: listings, decision pages and the pages about the site
   answered 200, no login or challenge. No robots file, so no crawl delay.
2. **Lawful copying?** For research: copyright 3.1 allows reproduction "for
   personal, educational or research purposes". 3.2: any other purpose needs
   the Commissioner's prior written permission.
3. **Terms accepted?** The copyright terms and disclaimer. Keeping every
   decision for a product that may be sold is "any other purpose": **held**.
4. **Privacy and statute?** Consumers anonymised by letter; providers named
   under the Commissioner's naming policy (June 2023); End of Life Choice Act
   s 36; Privacy Act and Health Information Privacy Code. The lane keeps no
   heading, paragraph, consumer, family, label, age, condition or place beyond
   the provider; a named practitioner is a role and the policy's ground; a
   case study's address (its summary) is private.

Position: `registers/hdc_decisions/position/hdc-decisions.md` (the integrator moves it).

## Done

- The lane, proved on real pages in the sample database (36 requests, 5 s
  apart, daytime): capture (year listings from 2017, case studies; a 403,
  429, 5xx or challenge stops the run; resumable), four profiles v1, reader
  (no model), load, publish, check, sample (12 pages), pane, spec. 35 fast
  tests, 16 mutants, a planted consumer detail refused by reader and check.
- The Commissioner's count: 168 listing pages, 2,010 decisions since 1998;
  2017: 49 (5 pages).

## Waits

- Arthur: `docs/decisions/queue/whether-the-hdc-decisions-may-be-copied-for-the-estate.md`
  (no default). Card `the-hdc-lane-is-held-on-the-commissioners-copyright-terms`.
- Once authorised: the `authorised:` line, the two jobs into the catalogue,
  the first night, then template 11's `hdc-decisions` check.
- Known limits: findings headed only as an issue keep their outcome, not the
  issue; a no-breach decision and a named practitioner are tested on invented
  pages only (none in the sample).
