# gazette: where it stands

**Date:** 2026-10-20. **Step:** 4.1, Gazette notices, `registers/gazette/`.
**Merge requests:** `gazette-1` (merged), `gazette-2` (raised).

## Done

- Capture: every Gazette notice the old estate holds as text, exported once
  (20 October 2026 04:49, `gazette-notices-2026-10-20.jsonl`, sha256
  47de7e09…, 207,133 notices 2000 to 16 October 2026); typed by the
  Gazette's own section code. Never run at load.
- Celebrant lists (gazette-1): 2,975 notices, 123,187 rows, 8,943
  addresses in `gazette_private` only.
- Director prohibitions (gazette-2, profile `gazette-director-prohibition`
  proposed): 537 notices, all read; 538 people, 538 addresses in
  `gazette_private` only; six actions (prohibition, court order, banning
  order, substitution, variation, revocation); the 3 notices a later one
  revokes or varies are marked, and a revoked notice's person is not
  published.
- Liquidator appointments (gazette-2, profile
  `gazette-liquidator-appointment` proposed): 43,587 notices (`al`), 43,478
  read (700 with a part set aside), 109 set aside; 60,711 company rows
  (15,646 from 2019), 45,067 liquidator rows; no address read.
- Outside check (`check.py`, exits 1): celebrant "Notice No." per series;
  531 titled prohibitions read; the prohibition cross-references held and
  marked; every `al` notice taken by its profile. Green on all 207,133.
- Full load into a scratch schema: 32 s.

## Carded

- `the-gazette-lane-leaves-the-other-insolvency-bankruptcy-and-appointment-notices-unread`.
- `liquidator-appointments-are-checked-only-against-the-gazette-s-own-section-code`.
- From session 1: `twelve-printed-celebrant-tables-are-unread`,
  `civil-union-celebrant-lists-without-stops-are-unread`,
  `the-old-capture-missed-a-seventh-of-2019-s-gazette-notices`.

## Next

1. The printed celebrant tables, by the organisation vocabulary.
2. The parties lane takes this lane's `au` notices instead of its export.
3. `ds` and `aw` company lists, then `ar`, `ba`, public appointments.
4. When the companies lane merges: the liquidations' outside check against it.
