# disclosures: where the lane stands

Step 4.1, the large-donation disclosures lane, `registers/disclosures/`.
Session 1, 19 October 2026, node2, Opus, working copy `disclosures`.

## Done (tranche 1, committed)

- The lane reads the Commission's own table of large declarations, both
  pages, all three regimes (2008-2010 over $20,000; 2011-2022 over $30,000;
  2023 on over $20,000): 520 declarations, 0 set aside, the catch log
  reconciles. Taken by hash from the old `var/staging/ec-donations/`
  (`index/` listings, `residue/donations_20k/`, `archive/2026-20k+-…`);
  nothing fetched. 281 scans held; all 276 rows from 2023 on joined to
  their scan by the Commission's link; 6 held scans no row links (listed in
  `files`, not read into rows).
- Amendment notes read as stated (9 amended, 1 withdrawn from 2023; 14
  amended and 2 `unread` "revised" notes before). Both dates kept.
  Addresses only in `disclosures_private`.
- Frozen site: 15 of 16 party-years equal; National 2023 differs by the
  old estate's double count (card
  `national-2023-the-frozen-site-counts-one-declaration-twice`).
- Proposed profile `ec-disclosure-listing` v1 in the lane folder
  (`profile-proposed.jsonl`): the integrator appends it to the ledger.

## Next (tranche 2)

- The form's printed total, from stored GLM-OCR readings (30 of 281 scans
  have one, under profile v2), against the table's amount; ask for re-reads
  of the rest.
