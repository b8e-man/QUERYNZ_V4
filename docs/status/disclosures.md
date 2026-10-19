# disclosures: where the lane stands

Step 4.1, the large-donation disclosures lane, `registers/disclosures/`.
Session 1, 19 October 2026, node2, Opus, working copy `disclosures`.
Merge request `disclosures-1` raised (branch `session/disclosures`).

## Done

- The Commission's own table of large declarations, both pages, all three
  regimes (2008-2010 over $20,000; 2011-2022 over $30,000; 2023 on over
  $20,000): 520 declarations, 0 set aside, the catch log reconciles.
  Copied by hash from the old `var/staging/ec-donations/`; nothing fetched.
- 281 scans held; all 276 rows from 2023 on joined to their scan by the
  Commission's link (the anchor carrying text); 6 held scans no row links.
- Amendment notes read as stated; both dates kept; addresses only in
  `disclosures_private`.
- Frozen site: 15 of 16 party-years equal; National 2023 is the old
  estate's double count (card; queue question, default no fix).
- Form check: 25 equal, 0 differ, 4 no legible total, 247 no reading yet.

## Waiting on others

- The integrator: append the proposed profile `ec-disclosure-listing` v1
  (`registers/disclosures/profile-proposed.jsonl`) to the ledger and delete
  the file; add and install `qv4-disclosures-read` and queue it for the
  scans with no reading (card `the-disclosure-scans-need-their-page-readings`).

## Next

- After the readings land, the lane's next load fills `form_check`
  unchanged; any `differs` is a card.
- Take over the old feed only on Arthur's word (step 4.1, step 4.8).
