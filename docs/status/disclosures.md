# disclosures: where the lane stands

Step 4.1, the large-donation disclosures lane, `registers/disclosures/`.
Session 2, 20 October 2026, node2, Opus, working copy `disclosures`.
Merge request `disclosures-2` raised (branch `session/disclosures`).

## Done

- The Commission's own table of large declarations, both pages, all three
  regimes: 520 declarations, 0 set aside, the catch log reconciles.
  Copied by hash from the old `var/staging/ec-donations/`; nothing fetched.
- 281 scans held; all 276 rows from 2023 on joined to their scan by the
  Commission's link; 6 held scans no row links.
- Frozen site: 15 of 16 party-years equal; National 2023 is the old
  estate's double count (card; queue question, default no fix).
- Reloaded after row 97's readings (scratch schema): form check 223 equal,
  3 differ, 50 no total read, 244 no scan held (before 2023). Each differ
  carded after looking at the total box: a handwritten total misread
  (table right), a struck-out total taken (table right), and a May 2023
  row whose link opens a February declaration (the Commission's to say).
- `qv4-disclosures-read` reads on the worker's card: `read_scan` and
  `main` pass `QV4_MODEL_URL` and `QV4_MODEL`, and `main` refuses without
  them (card `the-disclosures-read-job-reads-through-the-carve-out-s-server`
  closed).

## Waiting on others

- The integrator: merge `disclosures-2`. The job may be queued again for
  new scans; nothing is waiting on it now.
- Arthur: the May/February link (card
  `a-may-2023-declaration-links-the-scan-of-a-february-one`) needs the
  Commission's word if it is to be settled.

## Next

- The 50 "no total read": measure why (layout, handwriting, an empty box)
  before any change to `form.total`.
- The struck-out case: let the check say "equal, a second figure in the
  box" where one of two figures equals the table (card).
- Take over the old feed only on Arthur's word (step 4.1, step 4.8).
