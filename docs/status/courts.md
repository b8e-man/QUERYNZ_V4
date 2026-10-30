# courts: where it stands

**Date:** 2026-10-30. **Step:** 5.4 items 2 and 3, `registers/courts/`. **Session:** courts-2.
**Merge request:** `courts-2` (raised).

## Done

- One source (rulings 126, 127): the MCP's courts corpus as `support/mcpsource` landed it, 5,611 records
  (case pages 2,694; `judgment_pdf` 2,685; media releases 232), each file by hash. Nothing fetched;
  `qv4-courts-capture` retired; the old capture tables gone; the old listing read only for the gap report.
- Recognised by shape before any reader, measured on every record (`profile-proposed.jsonl`, 11 lines):
  case pages 2,686; NZSC 1,803; NZCA 342; NZHC civil 147, criminal 32; other courts 6; media releases 287;
  counsel's submissions 166; hearing transcripts 83; case synopses 37; scanned 4. 13 files the pull caught;
  5 set aside (4 with no shape, 1 page without a case's headings). The MCP's kind is coarse: one
  `judgment_pdf` in six is a release, transcript, submission or synopsis.
- The case page read (court, case name, citation, case numbers, dates, judges, summary, result, links),
  joined to its PDFs by url and by `case_slug`; `courts.cases`, `courts.case_links`, `courts.documents`
  (every record, its outcome: read, waiting on a reader, set aside, caught).
- The text reader (`model_read.py`): Flash-Next through `support.modelclient`, one reading per document,
  stamped with the reader, the served model and the prompt's hash, stored by hash and replayed by every
  load; names with the role the text gives each, counsel for each party, a one-line summary →
  `courts.people`, published as `pub.court_people` for the links lane. The deterministic fields stay.
- Suppression reaches every name on every document of a citation and of its case page, model-read names
  and the case name included (`suppress.py`, the ledger, `check.py`).
- Fast tier green (84.6 s; one xfail: no stored text-reader reading yet). 48 tests.

## Waiting

- The integrator: append the 11 proposed profiles; add `qv4-courts-load`, `qv4-courts-read`,
  `qv4-courts-pages` (spec.md); queue the read pieces. Radiance was down all session, so no document has
  a model reading: every judgment is "waiting: text reader" until `qv4-courts-read` runs.
- The provider: 80 judgments of the old listing (NZCA 37, NZHC 43; 2025–2026) the corpus lacks (card).

## Carded

`the-mcp-s-courts-corpus-lacks-80-judgments-the-old-listing-names`, `four-courts-files-no-shape-recognises`;
open from courts-1: `waitangi-tribunal-reports-are-held-and-not-read` (the corpus has none),
`district-court-judgments-are-not-captured` (the corpus has none), `high-court-outcomes-are-not-read`.

## Next

1. After the merge and the first `qv4-courts-read` run: the people rows on live, the xfail turns green,
   `check.py` live; read the summaries and roles on ten documents against the PDFs.
2. The links lane reads `pub.court_people` (its own card, its session).
