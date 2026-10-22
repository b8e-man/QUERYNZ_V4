# fix-registers-iwi-directory-1: the iwi directory's first full walk reads green
branch: fix/registers-iwi-directory-1 (pushed, 596dd9c)
session: fix-registers-iwi-directory-1 (scope registers/iwi_directory/)
raised: 2026-10-23
claims: registers/iwi_directory/ (read.py, check.py, pane.md, sample.list, tests/test_iwi_directory_reading.py); lessons/a-lane-s-hand-picked-sample-misses-the-shapes-its-first-full-walk-prints.md; lessons/a-value-flagged-as-contact-shaped-is-looked-at-by-character-class-never-printed.md

## What it fixes

`qv4-iwi-directory-load` at 06:35 on 23 October: `RED, nothing published: 2384 entities, 3703 relations, 96
settlements, 14 set aside; 8 entities carry a role flag no rule names`. The board added `no region map or authority
list read`. A scratch build of the same walk (pass 1, 229 pages) gave the same counts, then showed what the
first red was hiding.

**(a) The eight `other:` flags.** All eight are one picture, `maunga_blue_sm.png`, alt "Ngā Iwi o Taranaki.", on the
post-settlement entity of each of the eight Taranaki iwi (Ngā Rauru Kītahi, Ngāruahine, Ngāti Maru, Ngāti Mutunga,
Ngāti Ruanui, Ngāti Tama, Taranaki, Te Atiawa). The line beside it says "Member of Ngā Iwi o Taranaki who negotiated
the Collective Redress Deed with the Crown for Taranaki Maunga". The site's own legend (`/glossary/`, entry
`glossary_44`) says: "the eight iwi of Taranaki jointly negotiated the Collective Redress Deed (Te Ruruku
Pūtakerongo) with the Crown for Taranaki Maunga … signed on 1 September 2023". This is a role flag, not
decoration. It is now named `member of Ngā Iwi o Taranaki (Taranaki Maunga collective redress)`. It makes no
settlement row, because the entry names a membership and not this entity's own settlement.

I counted every picture in every organisation entry on all 229 pages: 13 file names, all role badges, none
decorative, and no contact icon (phone, email, address). The count also showed that `rma_sm_hapu` (37 times:
"groups that represent hapū of this iwi for the purposes of the RMA") and `rma_sm_other` ("other iwi
authorities") were being labelled "RMA iwi authority". The rule took only the first word of the file name. Both
are now named. A picture whose file name says phone, mail, address or contact, and which no rule names, is
dropped and never kept (hard limit 15).

**(b) `read_pages.iwi_links` empty.** The walk, the frontier and the page shapes were all fine. On the live walk
the 13 region maps link 127 times, the 84 authority lists 442 times, and between them they link all 117 iwi. The
cause was that the load refused at (a) and published nothing. The board's module check reads the published
ledger, which was still the empty table from the merge, so it reported "no region map read". `check.outside` now
says `a finished walk is held and none of it is published` when that happens. It also takes `--capture-database`
/ `--capture-schema` (the same options as load.py), so a scratch build of the live walk can be checked.

**(c) Hidden behind (a): 14 iwi pages set aside.** Fixing the flags alone would have left the outside check red
at 103 of 117. The pages use three table shapes that weren't in the sample: a list of hapū on its own, with the
marae in a separate table (Muaupoko and 10 more); Hapū | Marae | Location with no wharenui column (Ngāti Apa, Te
Patukirikiri); and Marae | Location (Ngāti Mutunga o Wharekauri). All three are now read. Marae on a page with
no hapū column belong to the iwi, as before.

**(d) Also found in the full walk.** "Not yet identified" was being read as a marae (2) and as a hapū (1); it is
now a blank. One trust's printed "Website" was three email addresses behind `http://`, and the reader took it as
a link. Any kept label whose value is shaped like an email or phone number is now dropped and counted as
`<label> (a contact printed in it)`.

## Proof

- Scratch build of the full live walk (`python -m registers.iwi_directory.load --schema
  scratch_fix_registers_iwi_directory_1`): 229 pages, 0 set aside, 2,696 entities (117 iwi, 1,381 hapū, 1,013
  marae, 97 organisations, 88 governance entities), 4,080 relations, 110 settlements. Lane check on it
  (`check --database querynz_v4_sample --schema scratch_… --views scratch_….v_ --capture-database querynz_v4`):
  117 linked, 117 read, **0 problems, exit 0**.
- The 522 email and phone runs printed on the 229 live pages appear in no row.
- Six new rules: the maunga flag, the RMA hapū picture, contact icon never a flag, contact value in a kept label,
  a hapū list on its own, no wharenui column with a placeholder. All six fail against the merged read.py. Six new
  mutants, each caught. The check's new "none published" line is tested.
- sample.list: four hard-case pages added (Taranaki, Muaupoko, Ngāti Apa, Ngāti Mutunga o Wharekauri). Sample
  now 40 pages, 14 iwi; the hard-case test asserts each.
- `bin/fast registers/iwi_directory`: **green in 43.2 s**. No model was used (ruling 79) and nothing was fetched.

## For the integrator

1. Merge. No schema, profile, job or catalogue change. The tables and views are unchanged and only the reading's
   rows differ. Profiles stay at v1: what each page kind is hasn't changed, only which tables an iwi page may hold.
2. Queue `qv4-iwi-directory-load` (or wait for its 06:35 run). The published ledger is empty, so it doesn't
   short-circuit as "unchanged". It should publish about 2,696 / 4,080 / 110, and the board's module check should
   then go green.
3. The sample database's `docs.names` now holds the four new pages' addresses. I re-landed their stored bytes
   against `querynz_v4_sample` (no fetch), because the live walk had written those names only to `querynz_v4`.
   Your refill needs nothing more.
4. Regenerate the lessons index for the two new lessons.

## Note for Arthur (hard limit 11)

While I was finding out why one row tripped the contact check, I printed that trust's website field with only
its digits masked. It turned out to be three email addresses, one apparently a named person's, and they appeared
in full in this session. They are in no file, row, card, commit or log. The second lesson records the safe way to
look. Earlier, my first page viewer masked links and digits but not the labels' values. It printed one
Taranaki trust's officer names (no phone or address) and the first ten characters of an organisation's role
mailbox. After that, the viewer masked every label's value.

## Result (integrator, 2026-10-23 09:27 NZDT)

Merged with the three other fixes of the morning as `integrate/fixes-2`:
`d710863 merge integrate/fixes-2: gate green` (fast tier green in 628 s on the
integrate branch; the gate's staging step loaded and published the touched
lanes). Branches and the working copy retired. Integrator items on the
branch: the board's windowed check takes the call the board makes (with a
registry test in checks/tests), `qv4-disclosures-load` in the catalogue
(priority 84, 18:40 UTC), the compare-gate card, board and lessons index
regenerated. The worker was stopped for the window and started after the
push.
