# Where the build stands

Overwritten at every close; under 3 KB. The detail is in `docs/merges/`.

**Date:** 2026-10-23, 02:12 NZDT. **Step:** 4 built through 4.4 and 4.9;
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
- Rulings 64 to 79 (`docs/decisions/rulings.md`); emergency fixes 76 and
  77 applied in the old repository 22 October, proved by the 06:19 release.

## Running (headless, from the integrator)

- Nothing. Merged 6.3 (capture only, ruling 79): `procurement-1` (GETS
  listing and councils' lists barred by terms; ACC's costs file),
  `councils-1` (minutes and interests registers held unread),
  `local-elections-1` (2,183 candidate returns listed, 1,603 held unread). Merged 21 to 22 October (`docs/merges/`):
  sanctions, scan, tenders (29,874 award notices), the
  regulators, oio, hdc, diaries, grants 1 and 2 (178,729 grants), the
  scan templates, redirects, `fix-support-db-1` (a session's owner login on
  the live database is refused; the gate and hand runs carry
  QV4_INTEGRATOR=1), `security-1` (track H.1 to H.3; sittings after the
  build, ruling 79), `settlements-1` (template 3: Te Kāhui Māngai walked
  weekly; Te Haeata behind a login, watched). Template 4 and step 7 wait.

## Half-done

- 4.5 (`comparison-1`, `-2`): day three 29,259 differences, 0 uncarded,
  not clean; ahead: seven clean days, checkpoint, export test, the switch
  after 7 November. Step 2: `qv4-questions` held (ruling 22); node1 setup
  carded (ruling 57).
- Waits on Arthur: node1's fence and the cable check; items 12, 69
  and 75 return after the build.
