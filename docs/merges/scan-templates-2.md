# scan-templates-2: step 6.2 template 3, the post-settlement governance map (use case 14), on the scan shape
branch: session/scan-templates-2 (pushed; d710163)
session: scan-templates-2 (Opus)
raised: 2026-10-23
claims: products/scan/templates/ (new: settlement-map-iwi, -settlements, -charities, -companies, -societies, -shareholdings, each template.toml + limits.md; _tests/test_settlement_map.py; _shape/scan-templates-2-shape.diff); docs/status/scan-templates.md; cards opened: blocker the-scan-templates-2-shape-diff-at-the-merge, findings a-settlement-key-names-several-rows and the-iwi-directory-key-folds-two-bodies-into-one (both for registers/iwi_directory); card closed: the-settlement-commitments-are-not-held (accepted onto the limits); queue a-named-use-for-the-200 updated (recommendation, default unchanged); one lesson

The question: "for each iwi organisation or post-settlement governance
entity in the iwi and hapū directory, which iwi and settlement does it stand
for, which charity and which company is it, and who holds its offices?" A
line follows one chain of rows, so it is six scans read together by the
body's directory key, each starting from the directory's 185 bodies (kind
organisation or governance entity):

1. **settlement-map-iwi**: body, its "organisation of iwi" listing, the iwi.
2. **settlement-map-settlements**: body, the settlement its own entry names
   (Act, deed or collective, the stage as printed; a mandate is a stage).
   Te Haeata is behind a login and not held; the limits say so.
3. **settlement-map-charities / -companies / -societies**: body, the
   register row of its name (by charity number or NZBN where both carry
   one: none printed today; else by folded name, near, namesakes marked),
   and each officer or director the register lists.
4. **settlement-map-shareholdings**: body, each holding filed under its name
   (suppressed holders never compared), the company held.

Every line graded, cited by document and dated; "none found in" kept;
licences and attribution on every read (Te Kāhui Māngai CC BY 3.0 NZ as
catalogued, position `iwi-and-hapu-directory`). Register scan only, never
the public site (6.2 row 3, 6.4, hard limit 14). No contact detail, address
or marae location read. The Māori Land Court and the Tribunal reports are
out by name. No model (ruling 79).

Checkpoint (real published tables, state in
`querynz_v4_sample/scratch_scan_templates_2`, the diff applied on a merged
copy): runs 18 to 23, 231 / 193 / 2,163 / 329 / 331 / 198 lines, 0
contested, 0 problems, the slowest 9.5 s; an independent recount (own fold,
views streamed) equal for all six, grades too; ten bodies read against
their stored directory pages (`settlement-map-iwi/limits.md`).
`python -m products.scan check` green over all eleven scans, 23.3 s; the
five earlier scans unchanged in lines and citations. Tests: the template
tests (fast, skip until the diff is in, guarded); in the diff 1 fast and 7
slow; 10 mutants (7 code, 3 rule), each caught; every `products/scan` test,
slow included, green on the merged copy. `bin/fast products/scan` green on
the branch, 41.6 s. The whole-repository `tests/test_generators.py` is red
only on the generated board, queue and lessons index (step 4 below).

## At the merge, please (card `the-scan-templates-2-shape-diff-at-the-merge`)

1. Apply `products/scan/templates/_shape/scan-templates-2-shape.diff` (10
   hunks: `views.py`, `template.py`, `lines.py`, `check.py`,
   `tests/test_lines_and_rules.py`, `tests/test_templates_real.py`; made
   against 9265192, checked by a strict reader to reproduce the merged copy
   file for file) in the same commit as the templates; delete
   `products/scan/templates/_shape/`. Without it the six templates do not
   load and `run --stale` fails loudly.
2. Fast tier; the slow `products/scan/tests/test_templates_real.py` (11 tests).
3. With `QV4_SCAN_STATE=querynz_v4/register_scan`: `python -m products.scan run`
   for the six `settlement-map-*` scans (about 20 s in all), then
   `python -m products.scan check`. The citation change re-numbers nothing
   in the earlier scans; their runs stand.
4. Regenerate the board, the lessons index and the queue. `lessons/INDEX.md`
   on the branch is the generator's own output (written when
   `tests/test_generators.py` ran `bin/lessons-index`; the hook refuses any
   edit of it, a restore included); regenerate over it as usual.
5. The scratch schema `scratch_scan_templates_2` in the sample database
   holds the checkpoint's runs; Arthur's drop.

Two findings for `registers/iwi_directory` (a fix session): a settlement key
names one row per body (the shape now cites per row, so the scan is right
either way); and `tkm/org/ngati-haua-iwi-trust` folds Ngāti Hāua Iwi Trust
and Ngāti Hauā Iwi Trust into one row.

Lesson: `a-citation-numbered-by-a-key-cites-the-first-row-where-the-key-names-several`.

## Result (integrator, 2026-10-23 10:46 NZDT)

Merged: `aef355f merge integrate/scan-templates-2: gate green`. Branch
`integrate/scan-templates-2` from `session/scan-templates-2` (d710163; main
was already in it). Card `the-scan-templates-2-shape-diff-at-the-merge`
closed: the diff applied by the integrator's own unified-diff reader (the
hooks refuse `git apply` and `patch`), six files, ten hunks, every context
line matched, `_shape/` deleted in the same commit as the six templates;
`bin/fast products/scan` green in 41.6 s and the slow
`test_templates_real.py` 11 green with the diff in. The six scans run on
`querynz_v4/register_scan` as runs 147 to 152: 231 / 193 / 2,163 / 198 /
329 / 331 lines, 0 contested, 0 problems, the checkpoint's counts. The
check then named one stale citation in `procurement-directors-donors`
(the integrator had reloaded `pub.disclosures` by hand at 08:35, so its
cited document hash had moved); `run --stale` re-ran the four scans that
read it (runs 153 to 156, lines unchanged) and `python -m products.scan
check` is green over all eleven scans. The `whenever` job that re-runs
stale scans covers the nightly disclosures load from tomorrow. Fast tier
green; gate green. Branches and the working copy retired. The two
`registers/iwi_directory` findings go to a fix session next. Arthur's: the
scratch schema `scratch_scan_templates_2` in the sample database.
