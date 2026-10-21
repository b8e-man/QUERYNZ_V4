# openlaw-1: the OpenLaw NZ lane, built and HELD on its API terms
branch: session/openlaw-1 (pushed; 410da57)
session: openlaw-1 (Opus)
raised: 2026-10-21
claims: registers/openlaw/ (capture, read, load, check, tables, publish, sample, sample.list, pane, spec, profile-proposed.jsonl, position/openlaw-case-law.md, tests); docs/status/openlaw.md; docs/decisions/queue/whether-openlaw-api-content-may-be-copied.md; cards/the-openlaw-lane-is-held-on-its-api-terms.md; lessons/read-an-interfaces-own-terms-before-its-capture-a-free-key-can-forbid-copies.md

Step 5.4 item 1. **The capture as briefed would break hard limit 4.** The
OpenLaw NZ API terms we accepted with the key (clause 3.6(a)) bar "scrape,
build databases, or otherwise create permanent copies" without OpenLaw's
express authorisation, and 3.7 bars charging for a service built on the
API. So, as the hard limits say, that piece stopped. It is in the decision
queue marked **no default**. Everything else is built and tested, and the
lane is held behind one setting. No case record has been landed.

## What the lane is

- **Hold:** `capture.authorisation()` reads an `authorised:` line from the
  position covering `api.openlaw.nz`. Without one, `capture.Run.run` raises
  `Held` before any request, and `capture.main`, `load.job` and
  `check.outside` report "held" (check: red). Granting it is a one-line
  edit to the position page.
- **Capture (once authorised):** the gated POST of one GraphQL query
  (`CASES_QUERY`: case fields, court, pdf, citations, cases cited, statute
  links, the party table; not counsel). Ten cases a page, newest first
  (`CASE_DATE_DESC, ID_DESC`), by offset, resumable. Serial, 3 s of rest
  and the gate's floor, off-peak 22:00–06:00. A 403, 429, 5xx, a challenge
  or GraphQL `errors` stops the night. Each page is landed verbatim by
  hash, with a listing (`capture_pages`: offset, sha256, the case ids).
  Passes: `sample` (2,000 cases, the first night), then `full` weekly and
  `head` nightly. The key is read at use and never printed or put in a URL.
  The interface's terms and mission pages land with the first run.
- **Read:** profile `openlaw-graphql-cases-page` v1 (`profile-proposed.jsonl`,
  **for the integrator to append to support/profiles**). Recognised by
  shape. One case row (neutral citation, court, registry, filing number,
  date, id, PDF address). One party row per name and role, from the
  interface's party table, or else from the caption grammar. Citation rows
  (citing, cited) and statute rows. The catch log has reasons. Newest
  landed page wins, older ones are superseded. No model reads anything.
- **Suppression (hard limit 16):** a case is suppressed when its text has
  one of ten named markers, its title has a marker, or a party is
  anonymised. Every non-Crown name and the title are then withheld on the
  views; the rows stay. Names and titles live in `openlaw_private` only.
  An anonymised party is never expanded. No address and no counsel are read
  (hard limit 15).
- **Publish:** `pub.court_cases`, `pub.court_case_parties`,
  `pub.court_case_citations`, `pub.court_case_statutes`.
- **check.py:** the outside figure (held against the count probed by
  offset at the pass's start, with today's count beside it), the ledger,
  parties per case, suppression counts, view leaks, and catch-log reasons.

## Verified

- `bin/fast registers/openlaw`: 57 passed, green, with the sample filled.
  This includes a seven-way mutant check of the suppression rule, which
  caught one weak property on its first run (fixed), and a `publish.sql`
  mutant that check.py must flag.
- Slow, against the real interface: the newest 3 cases were read in memory,
  kept nowhere, and every record was typed; the probe found 46,545 cases in
  17 requests. That is the old estate's August figure, so the corpus looks
  static.
- `python -m registers.openlaw.capture` → "held … nothing asked for or
  landed" (one run record line in live/checks/runs.jsonl).
- sample.list is empty on purpose (it says why).
- Whole-repository `bin/fast`: green in 326.7 s (the 300 s target missed, recorded by the tool).

## For the integrator

1. Move `registers/openlaw/position/openlaw-case-law.md` into
   `docs/legal/positions/`. Its hosts line names
   `s3-ap-southeast-2.amazonaws.com` for the terms PDF only. Narrow or drop
   it if you would rather not cover a shared S3 host; the capture needs it
   only to land the terms once.
2. Append `profile-proposed.jsonl` to `support/profiles/profiles.jsonl`.
3. Add `openlaw` to `support.db.LANES` (schemas `openlaw`, `openlaw_private`).
4. File the queue item and the card. Install no job: both
   (`qv4-openlaw-capture`, `qv4-openlaw-load`, in spec.md) wait for the
   authorisation.
5. Possible clash: `courts-1` may also want a `pub.court_*` name; these
   four views are prefixed `court_case*`.

Lesson filed: read an interface's own terms before its capture.

## Result (integrator, 2026-10-21 16:58 NZDT)

Merged into main as eeb4807 (`merge integrate/openlaw-1: gate green`). Branch `integrate/openlaw-1` from `session/openlaw-1` (410da57), main merged. The lane is HELD on the interface's terms (clause 3.6(a)/3.7): queue item `whether-openlaw-api-content-may-be-copied` stands with no default, card `the-openlaw-lane-is-held-on-its-api-terms` open. Integrator items: the position moved to `docs/legal/positions/openlaw-case-law.md` with the shared S3 host dropped from its hosts line (the terms PDF is landed by hand if the lane is ever authorised); profile `openlaw-graphql-cases-page` version 1 appended (76 slugs); `openlaw` in the lane list and its two schemas applied with grants on both databases; no job installed; the staging contract's `load` added to the lane's `load.py`, held with the capture (empty tables, nothing published, while the position carries no authorisation line); property-1's merge record; board, lessons index and queue regenerated. Fast tier green in 408.1 s (target 300 missed under load, recorded). Gate green; staging ran the held load: nothing read, nothing published. Branches and the working copy retired.
