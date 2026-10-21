# Where the build stands

Overwritten at every close; under 3 KB. The detail is in `docs/merges/`.

**Date:** 2026-10-22, 07:5x NZDT. **Step:** 4 built through 4.4 and 4.9;
4.5 day three not clean; 5.1 done; 5.2 closed (ten templates, `fix-report-2`
parameters); 5.3 eight lanes merged (OpenLaw, HDC held on terms; sanctions
lists held); 5.4 merged; 5.5 merged; 6.1 merged (`scan-1`, the scan on
port 8450); 6.2 `tenders-1` merged, templates 1 and 2 merged (`scan-templates-1`);
6.3 `grants-1` merged (178,729 grants live). Track C measured; B and E closed. **Boxes:** node2 is the estate; node1 waits for its setup
card (ruling 57). **Alarm channel:** the old estate's ntfy address.

## Done

- Steps 0 to 3 closed (`docs/merges/scheduler-*`, `trial-*`; ruling 60).
  1.4's positive half observed 21 October (ruling 70: the gap stands).
- 4.1, fifteen lanes merged (`docs/merges/`): the political-donation
  lanes (ruling 66 reconciliation, `reconcile-1`), parties, party finance,
  gazette 1 to 6 (207,133 notices), house, companies (1.92 M), expenses and
  interests, societies, candidate returns, charities (46,131; ruling 64),
  party boards (`party-boards-1`, ruling 72: built, not on the site),
  OpenLaw (`openlaw-1`, HELD on its terms), courts (`courts-1`, 148 judgments).
- 4.2/4.3 links: 2.82 M links, 2.32 M groups, rebuilt after `coupled-1`
  (ruling 73); the agent (track C) scores and applies nothing (ruling 69).
  4.4 site version 3. 4.9 board 78 views. 5.1 the report shape, tranche 3.
- 5.2 closed: templates 08, 04, 03, 02, 13, 07 (ruling 65), 05, 06, 11
  (`healthcare-1`), 12 (`property-1`). 5.5 `qv4-companies-monitor`.
- Rulings 64 to 78 on 21 October (`docs/decisions/rulings.md`); the two
  emergency fixes (76, 77) applied in the old repository 22 October 05:12,
  aefd8d0b to 7f4a88c6; proof: the 06:19 release.

## Running (headless, from the integrator)

- `security-1` (track H.1 to H.3, Fable). Merged since 18:00 on 21 October:
  `sanctions-1`, `scan-1`, `tenders-1` (29,874 award notices live),
  `regulators-1`, `fix-report-2`, `oio-1`, `hdc-1`, `diaries-1`,
  `grants-1` (178,729 grants live), `fix-support-fetchgate-1`,
  `scan-templates-1`, `fix-templates-1`, `redirects-1`,
  `fix-products-templates-1`, `grants-2`, `fix-support-db-1` (a session's
  owner login on the live database is refused; the gate and hand runs
  carry QV4_INTEGRATOR=1). Next: template 3's sources as a lane;
  template 4 waits on the diaries source. Step 7 held.

## Half-done

- 4.5 (`comparison-1`, `-2`): day three 29,259 differences, 0 uncarded,
  not clean; ahead: seven clean days, checkpoint, export test, the switch
  after 7 November. Step 2: `qv4-questions` held (ruling 22); node1 setup
  carded (ruling 57).
- Waits on Arthur: the OpenLaw and HDC
  terms (no default), the letters (Ministry of Justice; MBIE on the GETS
  files; the Commissioner), the diaries source's name (ruling 78), node1's fence and the cable check; items 12, 69
  and 75 return after the build.
