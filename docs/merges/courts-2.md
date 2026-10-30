# courts-2: the courts lane reads the MCP's corpus only, every kind by shape, names by the text reader (rulings 126, 127, 128)
branch: session/courts-2 (pushed, 9c3122b; four commits on main's 6038992; main had moved to c7b8616, board only, at the first raising)
session: courts-2 (build, Fable, scope registers/courts/)
raised: 2026-10-30
claims: registers/courts/ whole: capture.py (the corpus's arrival record: `records`, `caught`, `old_listing_gap`; no fetch), read.py (`recognise` by shape, `case_page`, `sheet`, `read`, `read_pages`), model_read.py (new: the text reader's reading through `support.modelclient`, `--pieces`, `--piece <sha>`), load.py, suppress.py, check.py, tables.sql (**DDL: new tables `documents`, `cases`, `case_links`, `people`; `judgments` gains `case_slug`; the capture tables `captures`, `feeds`, `capture_log` are gone**), publish.sql (new views `pub.court_people`, `pub.court_cases`, `pub.court_case_links`, `pub.court_documents`; `pub.court_judgments` gains `case_slug`), caption.py (citation regex admits `NZEmpC`), sample.py, sample.list (22 corpus records: the case page the corpus holds under two urls joined it), profile-proposed.jsonl (11 lines), spec.md, pane.md, README.md, tests (test_courts_capture.py deleted; test_courts_shapes.py and test_courts_model_read.py new; test_courts_lane.py rewritten); docs/status/courts.md; two cards; one lesson (regenerate lessons/INDEX.md and the card board at the merge).
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

Fast tier for registers/courts: green in 86.5 s (target 60 s missed, recorded; the sample fill takes 43 s), 50 tests, one xfail (`test_courts_lane`: the text reader's rows, which pass once a sample document has a stored reading). Each tranche's tests fail on main (the modules `model_read`, `recognise`, `case_page` do not exist there; the lane test asks for the corpus records). `check.py` green on the sample ({"parsed": 10}; caught 2, set aside 1, waiting on the page reader 1; the lever across a case reaches 3 documents). Root checks: the lane shape test green. The full corpus was built with the branch's code into `scratch_courts_2_full` of the sample database (the live owner login is refused to a session by `support.db`'s guard; the records came from the live store through the read-only login, the files from the document store): figures under Result.

## Carded

- `the-mcp-s-courts-corpus-lacks-80-judgments-the-old-listing-names` (NZCA 37, NZHC 43, 2025–2026; for the provider).
- `four-courts-files-no-shape-recognises`.

## Not built

No District Court, no Waitangi Tribunal (the corpus has neither; their courts-1 cards stay open). No reading of a High Court outcome beyond the model's summary. No change outside `registers/courts/`.

Lesson: `a-source-s-kind-field-is-a-hint-recognise-every-document-by-its-own-shape-before-building-its-reader`.

## Result (30 October, 18:44: refused)

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

## Result

Raised again 30 October 2026, 19:04, from session/courts-2 at 9c3122b (one commit on 0e9f54f, all inside
`registers/courts/`; profiles and catalogue untouched, `profile-proposed.jsonl` unchanged).

What changed. A document is its bytes: `read.read` reads one entry per file (`_primary_entries`: the record with the
plainest url, no query string, then the shortest, then the lowest id), so a case, its links, a judgment, its parties,
paragraphs and people are emitted once however many records point at the hash; every sharing record is still its own
`documents` row carrying that reading (`read.SHARED_READING`), with its own catch-log line where the file was set
aside or caught, and `counts["shared"]` says how many. `read._once` asserts every key of every table once before the
COPY. `check.py` counts the records sharing a file and fails on a file with two case or judgment rows. The unit test
`test_a_file_under_several_records_is_read_once_and_every_record_s_row_carries_the_reading` fails on 0e9f54f (two
cases rows, two judgments, four parties from seven records) and passes here; the sample now holds the live pair (the
case page with and without `?searchterm=None`) and the lane test asserts one case row for the two records. The other
keys were looked at: `documents` is keyed by record id (one per record already), `people` was built from a dict by
hash (once already), `set_aside` has no key; `judgments`, `judgment_parties`, `paragraphs` and the private
`withheld_names` collided the same way as `cases` and `case_links` and are fixed by the same change (the 2006 NZCA
judgment under `…limited.pdf` and `…limited_000.pdf` was the judgment pair on live).

The full corpus, built twice with this code (204 and 208 s; `scratch_courts_2_full`): records 5,611 (5,611 taken by the
pull), every one accounted for: waiting on the text reader 5,589, on the page reader 4, set aside 5, caught 13;
records sharing a file 3 (the three hashes of the refusal, each under two records, outcomes equal within each pair).
Profiles: case pages 2,686; NZSC 1,803; NZCA 342; NZHC civil 147, criminal 32; other courts 6; media releases 287;
submissions 166; transcripts 83; synopses 37; scanned 4; none 18. Judgments 2,329 (parsed 2,224, partial 24, unparsed
81; NZSC 1,788, NZCA 340, NZHC 178, NZEmpC 4, NZREADT 1, unread court 18); parties 7,870 (withheld 578, anonymised
303, Crown 1,124); cases 2,685 (1,628 with a citation, 1,644 with a judgment date), links 4,548 of which 2,922 to a
held file; suppression: 445 judgments flagged (banner 404, order in the text 134, CPA s 203 153, …), 483 cases
withheld, 1,061 names in the private table, no ledger order; catch log 202 lines (listing 80, parse 105, read 79,
pull 26, recognise 5); the old listing's gap 80. People 0: no document has a text-reader reading until
`qv4-courts-read` runs.

The check found a second thing the gate would have hit after the COPY: 23 of the 200 sampled judgments short on the
counsel-role rule (tolerated 2). 22 were Supreme Court criminal leave judgments of 2004 to 2012: the caption "X v THE
QUEEN" prints no role (the reader's criminal shape names the sides Prosecutor and Defendant) and the counsel lines say
"for Applicant" and "for Crown". `caption.roles_unaccounted` now holds the stage's words by the criminal caption's
two sides (an ordinal by that many defendants; any other word still reported) and `check.roles_short` passes the
caption shape through; a caption test covers it. Roles short now 1 (a party "in person" beside plural respondents),
within the tolerance. The second build's check: green, no failure line (the first's one failure was this rule).

Fast tier green, 86.5 s, 50 tests, one xfail (as before). Nothing fetched; no name or address printed.

## Result (integrator)

Merged 30 October 2026, 19:40, as 7cdc8ab (integrate branch 7d50baf on the session's 9c3122b; gate green: every
test, every slow test since the catalogue and the profiles file changed, the staging load in 206 s and published:
records 5,611, waiting on the text reader 5,589, on the page reader 4, set aside 5, caught 13, shared 3, judgments
2,329, parties 7,870, cases 2,685, withheld 1,061, listing gap 80). Three gates: 18:11 refused on
`support/profiles/tests/test_profiles.py`, which pins the shipped profile count (146 → 153 for the seven new slugs,
moved in an integrator commit); 18:44 refused on the staging load (`cases_pkey`, above; the session fixed it,
9c3122b); 19:12 green. Each gate ran with `QV4_LIVE` on a mirror of the live folder without the night marker (the
window was open; the scheduler's fast tests read it otherwise: card). Integrator commits: the 11 profiles appended
and the proposed file removed; `qv4-courts-capture` out of the catalogue, `qv4-courts-load` (04:40 NZDT),
`qv4-courts-read` and `qv4-courts-pages` in at priorities 32, 26 and 27 (85 and 22 were taken; check green, 89 job
types); `docs/status/courts.md` trimmed from 4,548 bytes to 3,000; lessons index and board regenerated. Pushed and
released (no worker restart owed: the catalogue reloads on the probe's clock; no systemd timer exists for a due job,
the worker runs them). Queued 19:43: `qv4-courts-read` row 865 with 5,589 pieces and `qv4-courts-pages` row 866 with
4. Neither runs until its card is free: the night window holds the page reader for the candidate-return backlog and
Radiance (text-reader) is down until it closes. The new views go on the board in the next merge (ruling 123).
Working copy `courts-2` and the local branch retired; `session/courts-2` on the remote is Arthur's to delete.
