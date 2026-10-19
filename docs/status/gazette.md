# gazette: where it stands

**Date:** 2026-10-20. **Step:** 4.1, Gazette notices, `registers/gazette/`.
**Merge requests:** `gazette-1`, `gazette-2` (merged), `gazette-3` (raised).

## Done

- Capture: every notice the old estate holds as text, exported once
  (207,133 notices, sha256 47de7e09…); typed by the Gazette's section code.
- Celebrant lists: 2,975 notices, 159,502 rows (the twelve printed tables
  now cut by the organisation vocabulary: 36,315); addresses private.
- Director prohibitions (537 notices) and liquidator appointments (43,587).
- gazette-3, each its own profile (proposed), measured on every notice:
  removals `ds`, winding-up applications `aw`, receiverships `ar`, notices to
  creditors `md`, administrations `aa` (1.48 M company rows in
  `company_notices`, receivers and administrators in `practitioners`);
  bankruptcies `ba` (65,299 people, addresses in `gazette_private` only,
  annulled people withheld); appointments to public office (3,155).
- Every company row joined to `pub.companies` (`register.py`): al 98.2%,
  ds 96.7%, aw 96.0%, md 93.8%, aa 91.9%, ar 90.9%; the rest catch-log lines.
- Outside check (`check.py`, exits 1): the floors above; every notice under
  al, ds, aw, ar, md, aa, ba and every "Appointment…" taken by its profile;
  "Honourable" appointees since 2021 against the house lane's members
  (125 of 134); table people named by a delimited list (79.7%).
- Full load into a scratch schema: 88 s, 4.5 GB peak.

## Carded

- `appointment-notices-whose-appointees-run-together-are-unread`.
- `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`.
- `bin-fast-runs-the-system-python-in-a-working-copy-without-a-venv` (integrator).
- From before: `civil-union-celebrant-lists-without-stops-are-unread`,
  `the-old-capture-missed-a-seventh-of-2019-s-gazette-notices`.

## Next

1. The parties lane takes this lane's `au` notices instead of its export.
2. The two cards above, if Arthur wants appointments or annulments shown.
3. The remaining unread sections (`ot`, `is`, `ct`, `cb`, `pn`, …), by
   use case.
