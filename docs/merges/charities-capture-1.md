# charities-capture-1: the Charities Register's feed, captured through the fetch gate
branch: session/charities-capture (pushed; 2a9787e)
session: charities-capture (Opus)
raised: 2026-10-20
claims: registers/charities/ (capture.py, read.py, tables.sql, spec.md, sample.list, position/, tests/); docs/status/charities.md; three cards; one queue question; one lesson

The capture half of step 4.1's charities lane. The source is the register's
open data feed, OData v2 at `www.odata.charities.govt.nz`: no login,
CC BY 3.0 NZ, 1,000 rows per query. Every keyed set (Organisations,
vOrganisations, Officers, AnnualReturn, Groups, the related-party
transactions, and the four free-text lists) is paged by key at that cap. Each
page is landed verbatim by sha256, listed in `charities.capture_pages`, with
failures in `capture_set_aside`. Passes resume after a stop; changes are
asked by `ModifiedOn`, with a full copy every 28 days. The code lists and the
seven documents about the feed (its metadata, the terms, the dictionary and
the diagram) are fetched weekly. Off-peak only, 5 s rest, and a failed read
stops the run. `read.py` lists and reconciles only; the reading is the two
builds' work (`read.pages(conn, set)`).

The register's own counts, 20 October about 07:30: 46,132 organisations
(29,265 registered), 589,015 officer rows, 430,434 annual returns, 357
groups. Landed by day as a proof (24 requests): 7 documents, 10 code lists,
Groups whole, 2,000 of 46,132 organisations. The rest waits for the job
(queue: `whether-the-first-charities-copy-runs-by-day`).

At the merge, please:
1. Add `qv4-charities-capture` to `support/scheduler/jobs.toml`
   (card `charities-capture-job-into-the-catalogue`, entry written out).
2. Move the draft position to `docs/legal/positions/` and set `POSITIONS`
   back to the default (card `charities-position-moves-to-the-legal-folder`).
   Until then the job runs as is: the gate reads the draft in the lane folder.
3. Regenerate the board, the queue roll-up and the lessons index (left
   uncommitted here; the hook keeps them out of a build session's commits).

The capture tables and the landed pages are already in `querynz_v4`
(`charities.capture_*`, `docs.*` source `charities`), as track E and the
earlier step 4 lanes did for their documents.

Fast tier: `registers/charities` 21 passed. Whole repository: green in 194 s
with the generated records regenerated in the tree (they go stale from the
new cards and queue file; not committed).
Lesson: `an-odata-count-obeys-the-feeds-row-cap`.

## Result (integrator, 2026-10-20 08:00 NZDT)

Merged into main as 6dda30f (merged main first). Done at the merge:
`qv4-charities-capture` in the catalogue at priority 34 (23:30 NZDT
nightly, four hours at most; `check` green, 37 job types); the position
moved to `docs/legal/positions/charities-register.md` and `POSITIONS`
set to the gate's default; the feed's host floored at 5 s in the gate;
both blocker cards closed; board, queue and lessons index regenerated.
Fast tier and gate green. The first full copy (about 1,170 requests, two
hours) runs on the job's clock tonight unless Arthur rules the queue
item `whether-the-first-charities-copy-runs-by-day`; after the first
night the capture check goes on the board. The two builds (charities_a,
Fable; charities_b, Opus) follow once the copy is complete.
