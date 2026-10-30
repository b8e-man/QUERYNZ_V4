# courts-2: the courts lane reads the MCP's corpus only, every kind by shape, names by the text reader (rulings 126, 127, 128)
branch: session/courts-2 (pushed, 0e9f54f; three commits on main's 6038992; main has since moved to c7b8616, board only)
session: courts-2 (build, Fable, scope registers/courts/)
raised: 2026-10-30
claims: registers/courts/ whole: capture.py (the corpus's arrival record: `records`, `caught`, `old_listing_gap`; no fetch), read.py (`recognise` by shape, `case_page`, `sheet`, `read`, `read_pages`), model_read.py (new: the text reader's reading through `support.modelclient`, `--pieces`, `--piece <sha>`), load.py, suppress.py, check.py, tables.sql (**DDL: new tables `documents`, `cases`, `case_links`, `people`; `judgments` gains `case_slug`; the capture tables `captures`, `feeds`, `capture_log` are gone**), publish.sql (new views `pub.court_people`, `pub.court_cases`, `pub.court_case_links`, `pub.court_documents`; `pub.court_judgments` gains `case_slug`), caption.py (citation regex admits `NZEmpC`), sample.py, sample.list (20 corpus records), profile-proposed.jsonl (11 lines), spec.md, pane.md, README.md, tests (test_courts_capture.py deleted; test_courts_shapes.py and test_courts_model_read.py new; test_courts_lane.py rewritten); docs/status/courts.md; two cards; one lesson (regenerate lessons/INDEX.md and the card board at the merge).
No DDL by hand: the load drops and recreates the reading's tables; `courts.suppression_orders` is never dropped.

## For the integrator, at the merge

1. Append `registers/courts/profile-proposed.jsonl` (11 lines: seven new slugs at version 1, the four court judgment profiles at version 2, signals carrying the measured counts) to `support/profiles/profiles.jsonl`, then remove the proposed file. `read.profile_version` takes the higher of ledger and proposed, so the order does not matter.
2. In `support/scheduler/jobs.toml`: remove `[jobs.qv4-courts-capture]` (retired, ruling 127; the installer removes its timer) and add the three below; `python -m support.scheduler check`; the installer.
3. The merge gate's staging step: `python -m registers.courts.load --schema staging_courts_load` (about 6 minutes; the check runs inside it and exits 1 on a failure; `--publish` to move it in). The first live figures land in the load's counts (`records`, `read`, `waiting: text reader`, `set_aside`, `pull_caught`, `old_listing_gap`); put them in the card board's line if you like, the status file carries the recognition pass's.
4. After the publish: `python -m registers.courts.model_read --pieces` prints one sha256 a line (about 5,600, judgments first, case pages last); enqueue `qv4-courts-read` with them. `qv4-courts-pages` for the 4 scanned documents (`--pieces` for it: the `documents` rows with outcome "waiting: page reader"). Radiance was down all session, so no document has a model reading yet; the night's load after the pieces run picks them up.
5. Catalogue the new views on the board in the merge after this one (ruling 123).

```toml
# ── step 5.4, the senior courts (courts-2; rulings 126, 127, 128) ──
[jobs.qv4-courts-load]
description = "Courts: rebuild the lane's tables from the MCP's courts corpus (every record a documents row: read, waiting on a reader, set aside or caught), replay the stored text-reader readings, publish pub.court_people and the rest on a green check. Nightly at 04:40 NZDT, after the pull."
needs = "processor"
memory_gb = 3.0   # unmeasured: the beehive load's figure; measure on the first night
deadline_s = 1800
query_timeout_s = 600
class = "due"
priority = 85
command = ["python", "-m", "registers.courts.load", "--publish"]
at_utc = "15:40"
nice = 10

[jobs.qv4-courts-read]
description = "Courts: the text reader's reading of one document (piece key sha256) through the text-reader profile: every person and body named with its role, counsel for each party, a one-line summary; stored by hash, replayed by the next load. Keys from python -m registers.courts.model_read --pieces."
needs = "model-profile"
profile = "text-reader"
memory_gb = 0.5
deadline_s = 900
query_timeout_s = 300
class = "whenever"
priority = 22
command = ["python", "-m", "registers.courts.model_read", "--piece"]
pieces = true
can_share = true
concurrency = 4

[jobs.qv4-courts-pages]
description = "Courts: the page reader over one document with no text layer (piece key sha256), every page as an image through the page-reader profile; the next load reads the stored pages."
needs = "model-profile"
profile = "page-reader"
memory_gb = 1.5
deadline_s = 1800
query_timeout_s = 300
class = "whenever"
priority = 22
command = ["python", "-m", "registers.courts.read", "--pages"]
requires = ["pdftoppm"]
pieces = true
can_share = false
concurrency = 1
```

## What it builds

One source. The lane's listing is the corpus's records in the document store (source `query-nz`, names `courts/<id>`, one entry per record id, the version the pull saw last, left-joined to `mcpsource.files` for the file's hash and state); its documents are the files the pull landed by hash. Nothing is fetched; capture.py fetches nothing and the test asserts no fetch code in the lane. The old listing (sha 8285d006…) is read for one thing: the judgments it names that no corpus record points at, by hash or url, each a catch-log line (`set_aside`, stage `listing`), never a row. The pull's own catch lines are lines too.

Recognised by shape before any reader (profiles before readers), measured on the 5,611 records of 30 October: case pages 2,686 (HTML with the courtsofnz `main`, `h1.case__title`, `h2` sections); NZSC 1,803, NZCA 342, NZHC civil 147 and criminal 32, other courts 6 under `courts-judgment` (a court line, numbered paragraphs, a JUDGMENT heading or caption labels); media releases 287; counsel's submissions 166; hearing transcripts 83 (`[year] NZSC Trans n` or speaker labels); case synopses 37; scanned 4 (a thin first page, to the page reader). 13 records have no file (the pull caught them); 5 are set aside at recognise. The MCP's kind is coarse: one `judgment_pdf` in six is not a judgment.

The case page is read deterministically (court from the breadcrumb, case name, citation and case numbers from the title, the summary, result, dates and judges from the sections, every link) and joined to its PDFs by url and by `case_slug`; `courts.cases`, `courts.case_links`. `courts.documents` carries every record with its profile, outcome, the sheet (citation, case numbers, date) and the model's summary.

The text reader (`model_read.py`): Flash-Next through `support.modelclient.chat` (local hosts only, the served model read back; thinking off), one reading per document stored under `reading_key(sha, 1, model, settings, profile, version)` with the prompt's hash in the settings, replayed by every load: names with the role the text gives each (party, counsel, witness, judge, company, agency, other), kind person or body, counsel for which party, a one-line summary. An answer with no usable JSON stores nothing and the piece fails. A document without a stored reading loads as "waiting: text reader" with its deterministic fields intact; the load never calls a model. Rows → `courts.people` → `pub.court_people` (name NULL when withheld, `suppressed`, document, page, place, reader, model, profile) for the links lane.

Suppression (unchanged in principle, wider in reach): a banner, an order in the text or a ledger order withholds the caption's names and every model-read name on every document of the citation and of its case page (judges, counsel, agencies and the Crown apart), and the case page's case name; `suppress.py`'s dry run reports the documents reached; `check.py` fails on a model-read name published on a reached document and on any withheld name in a published table.

## Checks

Fast tier for registers/courts: green in 84.6 s (target 60 s missed, recorded; the sample fill takes 42 s), 48 tests, one xfail (`test_courts_lane`: the text reader's rows, which pass once a sample document has a stored reading). Each tranche's tests fail on main (the modules `model_read`, `recognise`, `case_page` do not exist there; the lane test asks for the corpus records). `check.py` green on the sample ({"parsed": 10}; caught 2, set aside 1, waiting on the page reader 1; the lever across a case reaches 3 documents). Root checks: the lane shape test green. No live load was run (no owner session needed; the integrator's staging step is the first).

## Carded

- `the-mcp-s-courts-corpus-lacks-80-judgments-the-old-listing-names` (NZCA 37, NZHC 43, 2025–2026; for the provider).
- `four-courts-files-no-shape-recognises`.

## Not built

No District Court, no Waitangi Tribunal (the corpus has neither; their courts-1 cards stay open). No reading of a High Court outcome beyond the model's summary. No change outside `registers/courts/`.

Lesson: `a-source-s-kind-field-is-a-hint-recognise-every-document-by-its-own-shape-before-building-its-reader`.

## Result

REFUSED 30 October 2026, 18:44 (gate on integrate branch 594ae5b: every test green, including every slow test since
the catalogue and the profiles file changed; the staging load failed). `python -m registers.courts.load --schema
staging_courts_load` dies in the COPY into `cases` at line 1,886: `duplicate key value violates unique constraint
"cases_pkey"`, key `dfedba71…/case`. The cases key is the file's hash, and the corpus holds the same bytes under
more than one record: three landed hashes sit under two record urls each (one pair is a case page with and without
`?searchterm=None`), so two case rows carry one key. A first gate at 18:11 was refused on
`support/profiles/tests/test_profiles.py`, which pins the shipped profile count; the integrator moved the pin from
146 to 153 for the seven new slugs. The integrator's catalogue edits are ready to replay (the three jobs at
priorities 32, 26 and 27: the request's 85 and 22 were taken). The session is relaunched headless in its working
copy to key a case once however many records share its bytes, run the load against the live store before raising,
and raise `courts-2` again.
