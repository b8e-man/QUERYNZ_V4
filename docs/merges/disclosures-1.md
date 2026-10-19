# disclosures-1: the large-donation disclosures lane, from the Commission's own table
branch: session/disclosures (pushed; 48ad84b)
session: disclosures (session 1)
raised: 2026-10-19
claims: registers/disclosures/ (new `listing.py`, `form.py`, `load.py`, `profile-proposed.jsonl`; capture, read, check, tables, publish, sample, pane, spec, tests); cards `national-2023-the-frozen-site-counts-one-declaration-twice`, `the-frozen-site-shows-no-large-declarations-before-2023`, `the-disclosure-scans-need-their-page-readings`; lesson `the-first-link-in-a-commission-table-cell-is-not-always-the-row-s`; queue `fix-national-2023-on-the-frozen-site`; docs/status/disclosures.md

Step 4.1, the first lane. The lane reads the Commission's own table of
large declarations (`donations-exceeding-20000` and its `-30000` page) as
the old `ec-disclosures` job holds it under `var/staging/ec-donations/`,
copied by hash, read-only; it fetches nothing. The table is the source for
the fields it carries (Arthur, 29 September); the scanned declaration is
cited beside each row and its printed total checked against the table.

Measured over every held file (scratch schema, nothing live written):
520 declarations from 2 listings (276 from 2023, 220 for 2011-2022, 24 for
2008-2010), 0 set aside, the catch log reconciles. 281 scans landed; all
276 rows from 2023 joined to their scan; 6 scans no row links (listed in
`files`, never read into rows: which declaration they belong to is the
Commission's to say). Amendment notes read as stated, never inferred (9
amended, 1 withdrawn from 2023; 14 amended, 2 "revised" kept as `unread`
before). The 2023-on total, $14,714,081.38, equals the old table's to the
cent. Frozen site: 15 of 16 party-years equal; National 2023 differs by
$23,000, the old estate's double count (card; the lane's figure is the
Commission's). Form check: 25 equal, 0 differ, 4 no legible total, 247
no reading yet.

For the merge, please:
- Append `registers/disclosures/profile-proposed.jsonl` (profile
  `ec-disclosure-listing` v1) to `support/profiles/profiles.jsonl` with
  `add_version` and delete the proposed file; `read.current_profile()`
  takes the ledger's version first.
- The lane's tables are made again on every build (`create_tables` drops
  its own tables, CASCADE, then `tables.sql`); `publish()` does it inside
  one transaction and makes the views again. The schemas do not exist yet.
- After the merge: add `qv4-disclosures-read` to the catalogue and queue it
  for the scans with no reading (card `the-disclosure-scans-need-their-page-readings`:
  one piece per scan, `python -m registers.disclosures.read --scan SHA`,
  GLM-OCR). The next load picks the readings up unchanged. A build session
  does not queue live jobs.

Fast tier: `registers/disclosures` 23 passed with the sample filled (4.4 s);
whole repository: one red, `test_the_committed_records_generate_cleanly`,
the generated board, lessons index and queue, stale by this branch's card,
lesson and question; rebuilt at the merge. The working copy holds those
three regenerated files, not committed (the fence refuses them).

## Result (integrator, 2026-10-19 20:45)

Merged into main as 6afe3e1. Done at the merge: profile
`ec-disclosure-listing` v1 appended to `support/profiles/profiles.jsonl`
with `add_version` and the proposed file removed; the shipped-profiles
test now expects 23. The gate's staging load: 520 rows, 281 declarations
held, 276 linked, 6 files not linked, 0 set aside, published. After the
merge: `qv4-disclosures-read` is in the catalogue (priority 22,
page-reader profile, one piece per scan) and queued as row 97 with 246
pieces (every declaration at `no reading held`). The National 2023 queue
item is Arthur's.
