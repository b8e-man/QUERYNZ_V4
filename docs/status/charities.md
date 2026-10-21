# charities: where the lane stands

Session charities-3 (Opus), 21 October 2026, node2. Step 4.1: the capture and
the Opus build of the reading are one lane, `registers/charities`. The two
builds' folders and status files are gone (comparison: `docs/merges/charities-b.md`).

## Done (merge request `charities-3`)

- One lane: capture, `read.py` (listing and reading), `load.py`, `check.py`,
  `tables.sql` (capture's record never wiped; reading's tables rebuilt each
  load), `publish.sql`, `sample.py`/`sample.list` (both halves' cases),
  `pane.md`, `spec.md`, `profile-proposed.jsonl` (`charities-odata-page` v3).
- `load.publish` makes `pub.charities`, `pub.charity_officers`,
  `pub.charity_returns`, each row cited. Address for service in
  `charities_private.addresses`, shown only for a body corporate (queue
  default). Officers: no address, birth date or contact; a suppressed name
  blanked, row kept; a name field holding a date or an address withheld
  with a note (the Fable build's findings): 15 dates, 4 addresses.
- Capture: the register's registered count now lands with each full pass of
  Organisations; the feed's `datetime` literal is UTC (was NZ local).
- Full build: 46,131 charities, 589,108 officers, 430,437 returns, 357
  groups, 132 set aside; 1,079 pages reconcile; 60 s, 0.26 GB. check.py
  green: register 29,265 vs held 29,272 (+7 within 221 moved); view agrees
  on 46,121; live measure 29,272 = 29,272.

## Carried cards

- `a-charity-number-suffix-is-folded-by-the-shared-reading`: open, for `keys`.
- `the-charities-capture-lands-no-registered-count`: fixed here; the
  integrator closes it (text in the merge request). First real landing at
  the next full copy, about 17 November.

## Waits

- Integrator: `qv4-charities-load` into the catalogue (spec.md), the profile
  v3, the board views (pane.md), drop the scratch schemas (merge request).
- Arthur: the address-for-service ruling (queue); default applied.
