# disclosures-2: the read job reads on the worker's card; the form check filled
branch: session/disclosures (pushed; fcb028e)
session: disclosures (session 2)
raised: 2026-10-20
claims: registers/disclosures/read.py, registers/disclosures/tests/test_disclosures.py; cards `the-disclosures-read-job-reads-through-the-carve-out-s-server` (closed), `the-page-reader-reads-a-handwritten-50-000-as-59-000`, `a-struck-out-total-on-a-declaration-is-read-as-the-total`, `a-may-2023-declaration-links-the-scan-of-a-february-one`; lesson `look-at-one-box-of-a-form-by-cropping-at-its-label`; docs/status/disclosures.md

The read job: `read_scan` takes `url` and `model` and passes them to
`read_document`; `main` reads the worker's `QV4_MODEL_URL` and `QV4_MODEL`
and refuses (exit 2) without them, so a piece reads on the card its
worker holds and never falls back to port 8032, the carve-out's server.
The new test fails on the old `read.py` and passes on the new. The job
may be queued again; nothing waits on it now.

The reload, after row 97's readings (scratch schema of the sample
database, nothing live written, nothing fetched): 520 declarations, 0 set
aside, the catch log reconciles; form check 223 equal, 3 differ, 50 no
total read, 244 no scan held (the regimes before 2023). Frozen site
unchanged: 15 of 16 party-years equal, National 2023 the known double
count.

The three differs, each settled by viewing a crop of the total box alone
(no donor lines in the session): a handwritten "$50,000-00" read as
$59,000, table right; a struck-out $26,066.66 beside $19,250.22, the
check took the first, table right; a May 2023 row whose link opens a
February 2023 declaration of $116,162.00, the Commission's to say. All
three rows keep the table's figures. `form_check` "differs" still fails
the lane's outside check on the full run until those cards are settled;
the sample has none of the three.

For the merge: the fast tier is green (44.8 s) under the main venv's
python. `bin/fast` rewrote `docs/board.md` and `lessons/INDEX.md` in
this working copy; they are not committed, and the scope hook refuses to
restore them here.

## Result (integrator, 2026-10-20 04:15)

Merged into main as 04b64bd (merged main first; board and lessons index
regenerated). Fast tier and gate green; the gate's staging load: 520
rows, 281 declarations held, 276 linked, 6 files not linked, 0 set aside;
published. The carve-out card is closed: `qv4-disclosures-read` now reads
on the worker's card and may be queued again. The three `differs` cards
stand for Arthur and the Commission; nothing queued.
