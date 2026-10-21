# courts-1: the court judgments lane, its research note and profiles (step 5.4 items 2 and 3)
branch: session/courts-1 (pushed; head 89eab30)
session: courts-1
raised: 2026-10-21
claims: registers/courts (capture.py, caption.py, read.py, load.py, suppress.py, check.py, tables.sql, publish.sql, spec.md, pane.md, sample.list, sample.py, profile-proposed.jsonl, legal-position-court-judgments.md, research-legal-documents.md, tests); docs/status/courts.md; four cards; one lesson

**Ready to merge.** What it claims:

- **Held, never fetched.** The old estate's listing of its legal documents
  (`incoming_news.documents`: courtsofnz.govt.nz, waitangitribunal.govt.nz,
  districtcourts.govt.nz) exported once, 359 lines, pinned sha256 8285d006…
  (the bytes are in the store and in the session's scratch folder). Load
  copies each listed file by hash from `/home/user/querynz-data/documents/`
  (case 1 of 1.10): 353 true, 6 gone (catch-log lines). No District Court
  judgment is held.
- **Profiles before readers.** Five profiles, measured on every held
  document: `courts-nzsc-judgment`, `courts-nzca-judgment`,
  `courts-nzhc-civil-judgment`, `courts-nzhc-criminal-judgment`,
  `waitangi-tribunal-report`. The research note says what each format
  prints: citations, parties and roles, outcomes, numbered paragraphs,
  suppression markers.
- **The reading.** Deterministic, text layer only, no model: 148 judgments
  parsed, 0 partial, 0 unparsed; 590 parties, 166 marked low (wrapped lists);
  27 anonymised, kept as printed; 19,990 paragraphs indexed by page; the SC
  and CA outcome in a closed vocabulary (74 of 83). The Waitangi reports are
  recognised and set aside (card).
- **Suppression (hard limit 16).** A judgment with a banner, an order in its
  text, a ledger order, or another document of its citation that has one,
  publishes no party name but the Crown's and a printed initial: 60
  judgments, 89 names, held only in `courts_private.withheld_names`.
- **The lever.** `python -m registers.courts.suppress "<citation>|<sha>" --reason …`
  dry run by default, `--execute` records the order in
  `courts.suppression_orders` (never wiped, nothing deletes from it) and
  withholds across the lane's tables; every build reads the ledger, and
  `publish` applies it again after the swap. No unsuppress command.
- **Published:** `pub.court_judgments`, `pub.court_judgment_parties`.
- **check.py** (the outside check): every listed judgment a row or a
  catch-log line; parsed/partial/unparsed; per-field missing; suppression
  counts; no name under suppression; counsel roles held by the parties.
  Green on a full read into `querynz_v4_sample.scratch_courts_1_full`
  (counts above) and on the sample.
- **Tests:** `bin/fast registers/courts` green (61.7 s with the 30 s fill of
  every module's sample); the root suite green but
  `tests/test_generators.py::test_the_committed_records_generate_cleanly`
  (the board, lessons index: generated at the merge). Nine mutants of the
  grammar and the suppression rule are each caught.

**For the integrator, at the merge** (card
`the-courts-lane-s-edits-outside-its-fence`, six items): move the research
note to `docs/research/legal-documents.md` (the launcher's scope file did not
carry it, so the fence refused it); append the five profiles; move the
position to `docs/legal/positions/court-judgments.md`; add `"courts"` to
`support.db.LANES` and apply (the session reader must not get
`courts_private`); add `qv4-courts-capture` to the catalogue (the TOML is in
the card) and install; register the check. The load takes about 30 s.

Lesson: `a-judgment-s-citation-is-its-own-line-under-the-court-line-never-the-first-on-the-page`.
Nothing in the frozen estate touched; the old databases read through the
read-only login only; nothing fetched.

## Result (integrator, 2026-10-21 17:25 NZDT)

Merged into main as 9ae8b55 (`merge integrate/courts-1: gate green`). Branch `integrate/courts-1` from `session/courts-1` (89eab30), main merged. The six items of card `the-courts-lane-s-edits-outside-its-fence`, now closed: the research note moved to `docs/research/legal-documents.md` (its second paragraph rewritten to say so); the five profiles appended as version 1 (`courts-nzsc-judgment`, `courts-nzca-judgment`, `courts-nzhc-civil-judgment`, `courts-nzhc-criminal-judgment`, `waitangi-tribunal-report`; 81 slugs) and the proposed file removed; the position moved to `docs/legal/positions/court-judgments.md`; `courts` in the lane list, `courts` and `courts_private` applied with grants on both databases (the session reader never sees the private twin); `qv4-courts-capture` in the catalogue at priority 32 (the card's 34 is the charities capture's), nightly 03:30 NZDT, `support.scheduler check` green; the check needs no registration (`checks/module_checks.py` discovers every lane `check.py` with a `main`). The lesson's first line cut to 238 characters. Fast tier green in 469.1 s (target 300 missed under load, recorded). Gate green; staging loaded the lane from the held documents: 353 of 359 listed documents held (6 gone), 148 judgments parsed (0 partial, 0 unparsed), 590 parties, 89 names withheld, 205 Waitangi Tribunal documents set aside, and published `pub.court_judgments` and `pub.court_judgment_parties`; the two board views go in at the next merge (gate-order lesson). `qv4-board` restarted. Branches and the working copy retired. The Ministry of Justice letter stays Arthur's.
