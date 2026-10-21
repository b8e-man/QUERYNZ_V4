# openlaw: where the lane stands

Session openlaw-1 (Opus), 21 October 2026, node2. Step 5.4 item 1, the
OpenLaw NZ lane, `registers/openlaw/`. **Built and held.**

## The four questions (hard limit 4)

1. **Open?** Yes, with our own key (Arthur's sign-up of 15 August 2026,
   `openlaw_api_key` in the credential folder, read at use, never printed).
   No challenge or block; robots allows all, no crawl delay.
2. **Lawful copying?** The judgments carry no copyright (Copyright Act
   1994, s 27(1)). OpenLaw's parsing and graphs may be a compilation; the
   contract binds harder.
3. **Terms accepted?** The API terms (`apiterms.pdf`, `d327cea0…`) say in
   clause 3.6(a): no "scrape, build databases, or otherwise create permanent
   copies" without OpenLaw's express authorisation. 3.6(b) bars public
   display, 3.7 bars charging, and the mission page says non-commercial only.
   **The capture as briefed is barred.**
4. **Privacy and statute?** Suppression orders (Criminal Procedure Act
   2011 ss 200–211, family jurisdictions) bind every surface; Privacy Act
   2020 fairness; no address read.

Position: `registers/openlaw/position/openlaw-case-law.md` (the integrator
moves it).

## Done (merge request `openlaw-1`)

- The lane is complete on an invented fixture: capture, read, load,
  publish, check, sample, pane, spec, the proposed profile v1, and tests:
  57 fast tests (a 7-way mutant check of the suppression rule, plus the
  view's) and 2 slow ones against the real interface. The slow tests read
  in memory and keep nothing.
- The interface's figure: **46,545 cases** (probed by offset, 21 October;
  the same as on 15 August, so the corpus looks static).
- The capture and the load refuse while the position has no `authorised:`
  line. No case record has been landed.

## Waits

- Arthur: `docs/decisions/queue/whether-openlaw-api-content-may-be-copied.md`
  (no default). The card is `the-openlaw-lane-is-held-on-its-api-terms`.
- Once authorised: the first night (`--mode sample`, 2,000 cases), sizing,
  sample.list, and the two jobs into the catalogue.
