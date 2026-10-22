# Where the build stands

Overwritten at every close; under 3 KB. Detail: `docs/merges/`.

**Date:** 2026-10-23, 12:00 NZDT. **Step:** 4 built through 4.4 and 4.9;
4.5 not clean (no version accepted since 20 October, see Half-done); 5.1
done; 5.2 closed (ten templates); 5.3 eight lanes merged (OpenLaw, HDC held
on terms; sanctions lists held); 5.4, 5.5 merged; 6.1 merged (the scan on
port 8450); 6.2 `tenders-1` and templates 1 to 3 merged; 6.3's four source
lines have lanes. Track C measured; B and E closed. **Boxes:** node2 is the
estate; node1 waits for its setup card (ruling 57). **Alarm channel:** the
old estate's ntfy address.

## Done

- Steps 0 to 3 closed (ruling 60); 1.4's positive half observed (ruling 70).
- 4.1, fifteen lanes merged: donations (ruling 66, `reconcile-1`), parties,
  party finance, gazette (207,133 notices), house, companies (1.92 M),
  expenses and interests, societies, candidate returns, charities (46,131;
  ruling 64), party boards (ruling 72: not on the site), OpenLaw (HELD on
  its terms), courts (148 judgments).
- 4.2/4.3 links: 2.82 M links, 2.32 M groups, rebuilt after `coupled-1`
  (ruling 73); the agent (track C) scores and applies nothing (ruling 69).
  4.4 site version 3. 4.9 board 87 views. 5.1 the report shape, tranche 3.
- 5.2 closed (ten templates, ruling 65); 5.5 `qv4-companies-monitor`.
- Rulings 64 to 79; emergency fixes 76 and 77 in the old repository,
  proved by the 22 October release.
- Merged 21 to 23 October (`docs/merges/`): sanctions, scan, tenders,
  regulators, oio, hdc, diaries, grants, scan templates, redirects,
  `security-1` (H.1 to H.3), `settlements-1`, 6.3 capture only (ruling
  79: `procurement-1`, `councils-1`, `local-elections-1`), the fetch gate
  and scheduler fixes (a new job takes its next slot), `fixes-2` (the
  charities, overseas investment and windowed checks answer the board,
  the iwi directory's first walk reads green, `qv4-disclosures-load`
  nightly at 07:40), `scan-templates-2` (template 3, use case 14: six
  `settlement-map-*` scans, 3,445 lines, all cited and read back).

## Running (headless, from the integrator)

- Nothing. 11:51: the iwi directory's second sitting merged (a key per
  settlement row; two Hāua/Hauā trusts). Template 4 and step 7 wait
  (rulings 79, 63).

## Half-done

- 4.5: `qv4-site-build` has been refused by a gate since 20 October (card
  `the-site-build-s-compare-gate-…`): donor folds and key changes read as
  falls; 23 October the disclosures page's nightly hash (reloaded by hand,
  job added). Arthur's `--allow-drop` run accepts a version; then seven
  clean days, checkpoint, export test, the switch after 7 November.
  Comparison 23 October: 29,193 differences, 27 uncarded. Step 2: `qv4-questions` held (ruling 22).
- Waits on Arthur: node1's fence and the cable check; the site build with
  `--allow-drop`; letters (MBIE, Dunedin, the councils' returns and
  registers); scratch schema drops; items 12, 69 and 75 after the build.
