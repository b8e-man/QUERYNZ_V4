# fix-registers-iwi-directory-1 (second sitting): a settlement key names one row; two bodies under one key split
branch: fix/registers-iwi-directory-1 (pushed, 6905b50; two commits on aef355f)
session: fix-registers-iwi-directory-1 (scope registers/iwi_directory/)
raised: 2026-10-23
claims: registers/iwi_directory/ (read.py, load.py, check.py, tables.sql, publish.sql, pane.md, sample.list, tests/test_iwi_directory_reading.py); cards closed: a-settlement-key-names-several-rows, the-iwi-directory-key-folds-two-bodies-into-one; lessons/a-key-folded-from-a-name-can-merge-two-bodies-whose-names-differ-only-in-macrons.md

The first sitting's request (merged as `integrate/fixes-2`, d710863) is in `docs/merges/fix-registers-iwi-directory-1.md`.
This file replaces it in the inbox. When you commit this one, give it its own name under `docs/merges/` (for example
`fix-registers-iwi-directory-1-b.md`) so the first record is kept.

## Tranche 1: the settlements table (card a-settlement-key-names-several-rows)

- Each row now has its own `key`, the entity's key with the settlement's: `<entity key>|<settlement key>`. The
  settlement's own key moves to a new column, `settlement_key`, which every body whose entry names that settlement
  shares. The primary key is now `key` alone, where it was `(key, entity_key)`.
- When the post-settlement flag has nothing beside it ("Post-Treaty settlement governance entity.", on Hako Tūpuna
  Trust and Ngāti Porou ki Hauraki Rūnanga Trust), it names no settlement. The row stays, because the entry does say
  what the body is. Its `name` and `settlement_key` are NULL, its stage is the new value `settled: none named`, and its
  key is `<entity key>|no settlement named`. Before this fix the flag's own words were read as a collective
  settlement's name.
- The lane's check now goes red on a row whose key is not built from its entity and settlement, and on a settlement
  named by the flag's own words.
- Full live walk (pass of 22 October, 229 pages) built in scratch: **110 rows, 110 keys, 96 settlement keys** (the
  published table today has 110 rows and 97 keys). Stages: 69 Act, 16 mandate, 8 collective, 8 deed signed, 7 as
  printed, 2 none named. The Central North Island collective is now one `settlement_key` across 8 rows.

**`pub.iwi_directory_settlements` after the change**, in order: `key, settlement_key, entity_key, iwi_key, name, act,
act_year, stage, signed_on, as_printed, url, document, page, place, read_from, reader, profile, profile_version,
loaded_at`. The only new column is `settlement_key`, second. No column was renamed or dropped. Every `key` value
changes. publish.sql still uses `CREATE OR REPLACE VIEW`. That works because `load.publish` drops the tables with
CASCADE first, which drops the view too, so the new column order goes in cleanly.

## Tranche 2: the organisation key (card the-iwi-directory-key-folds-two-bodies-into-one)

- An organisation's key stays `tkm/org/<name folded>` (macrons off). The exception is a key whose pages print names
  that differ once the macrons are kept (`read.printed`; case and spacing are ignored). Then each printed name is its
  own body, keyed `<key>/<slug of the first page that prints it>`. The relations and settlements read from its pages
  go with it. This is done in `load.split_by_printed_name`, because the load is the only step that sees every page.
  The load's counts now include `organisation_keys_split`.
- On the full walk this happens to one key only. Of the 9 bodies listed on more than one page, it is the only one
  whose pages print different names. `tkm/org/ngati-haua-iwi-trust` becomes two rows:
  `…/ngati-haua-upper-whanganui` (Ngāti Hāua Iwi Trust, organisation, the mandate) and `…/ngati-haua` (Ngāti Hauā Iwi
  Trust, governance entity, the Ngāti Hauā Claims Settlement Act 2014).
- **One entity row changes key and becomes two** (2,696 to 2,697 entities: 98 organisations, 88 governance entities).
  **Relations and settlements follow:** the two "organisation of iwi" relations change `from_key`, and the two
  settlement rows change `entity_key` and `key`. I compared the scratch build with the live published views, and no
  other entity key or relation key moves.
- The pair is now a hard case. Both stored pages (`53c9af4a…`, `5c4d374d…`) are in sample.list, with a test on them. I
  ran that test's assertions against the earlier load: it produced one row named Ngāti Hāua with pages = 2, so the test
  fails on the old code. A second test uses invented pages and checks that the same name printed on two pages stays one
  body.

## Proof

- `python -m registers.iwi_directory.load --schema scratch_fix_registers_iwi_directory_1`: 2,697 entities, 4,080
  relations, 110 settlements, 0 set aside, 229 pages, 1 key split. The lane's check on it (`--database
  querynz_v4_sample --schema scratch_… --views scratch_….v_ --capture-database querynz_v4`): 117 linked, 117 read,
  **0 problems, exit 0**.
- New: two rules (the row key; the flag's own words) and two mutants, each caught. Two tests on the stored pages and
  one on invented pages. The sample grows from 40 to 43 pages: Ngāti Hako, plus the Hāua/Hauā pair. I re-landed their
  stored bytes into `querynz_v4_sample`'s `docs.names`. Nothing was fetched and no model was used (ruling 79).
- `bin/fast registers/iwi_directory`: **green in 42.2 s**. `bin/fast products/scan` green in 41.5 s and `bin/fast
  products/board` green in 41.6 s, on this branch.
- No contact value was looked at. The only rows printed were settlements, flags and organisation names.

## For the integrator

1. Merge. There is a schema change in the lane's own reading tables: `settlements` gains `settlement_key` and its
   primary key changes. The load drops and recreates those tables, so no migration is needed. Profiles stay at v1,
   because the page shapes are unchanged.
2. Queue `qv4-iwi-directory-load`. The walk is the same one that is already published, so the job will print
   "unchanged" and do nothing. To publish, clear `iwi_directory.read_pages` first (it is regenerable), or run the
   gate's staging and publish step. Expect 2,697 / 4,080 / 110, and the lane's check green.
3. **The board's catalogue** (`products/board/catalogue.py`) needs no change to work. Its Settlements join and parent
   use `entity_key`, which still matches the entity's key. It does not show `settlement_key`. If you want the board
   to show it, add `("settlement", "settlement_key")` to the view's `fields`.
4. **Template 3's six scans** need no code or template change. The settlements step joins `on = ["key",
   "entity_key"]` (the body's key to `entity_key`) and cites each row by its own key, document, page and place, which
   is now unique. Every settlement citation's key changes, and so do the Hāua/Hauā bodies, so after the load run
   `python -m products.scan check`. It will name the stale citations. Then run `run --stale` (or the six
   `settlement-map-*` scans) and `check` again. Expect 186 bodies where there were 185, and two lines that now read
   `settled: none named` where they read the flag's words as a collective.
   Three parts of products/ (yours, or a scan session's) now say things that are no longer true:
   - In `settlement-map-settlements/limits.md` and its `template.toml` limits: "a settlement's key is the
     settlement's, not the row's", the Hāua/Hauā line, the list of stage values (add `settled: none named`), and "185
     bodies (97 organisations)".
   - In `settlement-map-iwi/limits.md`: "the directory's key merges two bodies once", and the table row for Ngāti Hāua
     Iwi Trust.
   - The slow `products/scan/tests/test_templates_real.py::test_a_citation_names_the_row_it_read_…` looks for a
     settlement `key` with more than one row. It will now skip ("no settlement key names more than one row today").
     To keep testing what it was written for, point it at `settlement_key`: group by `settlement_key`, then cite each
     row by its own `key`.
5. Regenerate the lessons index and the board for the new lesson and the two closed cards.
6. The fast tier filled `scratch_fix_registers_iwi_directory_1` in the sample database with the sample build, over
   the full-walk proof. It is regenerable, and Arthur may drop it along with `…_private`.

## Result (integrator, 2026-10-23 11:55 NZDT)

Merged: `80f2dd3 merge integrate/fix-registers-iwi-directory-1b: gate green`
(fast tier green on the integrate branch; the gate's staging step loaded
and published the lane, so no `read_pages` clearing was needed). Branches
and the working copy retired. Integrator items on the branch: the board's
settlements view shows `settlement_key` beside each row; the slow citation
test in `products/scan/tests/test_templates_real.py` groups by
`settlement_key` and cites each row by its own key; template 3's
settlements limits (template.toml) say a row's key is its own and the two
Hāua/Hauā bodies are two, with the old wording kept as the first
checkpoint's record in each `limits.md` under a dated note. After the
merge: `python -m products.scan check` named 47 stale citations (every settlement row's key moved and the two bodies split); `run --stale` re-ran the six settlement-map scans (runs 169 to 174: 231 / 193 / 2,189 / 199 / 330 / 332 lines, 186 bodies, 0 problems) and `check` is green over all eleven. Published: 2,697 entities, 4,080 relations, 110 settlement rows under 110 keys for 96 settlements, 2 `settled: none named`; the lane's check 0 problems. The first gate run was refused: the catalogue field and the repointed slow test read `settlement_key` on the live view before the gate had published it (both reversed; they go in at the next merge, now a rule in docs/briefs/next.md).. Arthur's: the scratch schemas
`scratch_fix_registers_iwi_directory_1` and `…_private` in the sample
database. This record is the second sitting under this name; the first is
`docs/merges/fix-registers-iwi-directory-1.md`.
