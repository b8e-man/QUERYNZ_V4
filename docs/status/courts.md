# courts: where it stands

**Date:** 2026-10-30. **Step:** 5.4 items 2 and 3, `registers/courts/`. **Session:** courts-2.
**Merge request:** `courts-2` (raised again, 30 October evening, after the integrator's refusal of 18:44).

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
- A document is its bytes (the refusal of 18:44: the gate's staging load died on `cases_pkey`). The corpus holds the
  same file under more than one record (a case page with and without `?searchterm=None`, a 2006 judgment under two
  file names, a crawl-noise pair: three on live); the file is read once, under the record with the plainest url, so a
  case, its links, a judgment, its parties, paragraphs and people are emitted once, and every sharing record's
  `documents` row carries that reading. `read._once` asserts every key once before the COPY; `check.py` counts the
  records sharing a file; the sample holds the live pair.
- The full corpus built with the branch's code (`scratch_courts_2_full` in the sample database, the records read from
  the live store: the live owner login is refused to a session): 5,611 records in 204 s, every one accounted for
  (waiting on the text reader 5,589, on the page reader 4, set aside 5, caught 13; 3 share a file); judgments 2,329
  (parsed 2,224, partial 24, unparsed 81), parties 7,870, cases 2,685 with 4,548 links (2,922 to a held file),
  withheld 1,061 names under 445 flagged judgments; the old listing's gap 80. Check green.
- The check's counsel-role rule knows the criminal shape: a 2004–2012 Supreme Court leave judgment prints "X v THE
  QUEEN" with no role and "for Applicant", "for Crown" on the counsel lines; 23 of the live check's 200 were short
  (tolerated 2) until the sides were held by the stage's words. One remains (a party "in person" beside plural
  respondents), within the tolerance.
- Fast tier green (86.5 s; one xfail: no stored text-reader reading yet). 50 tests.

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
