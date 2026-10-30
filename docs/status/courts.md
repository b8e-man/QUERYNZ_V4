# courts: where it stands

**Date:** 2026-10-30. **Step:** 5.4 items 2 and 3, `registers/courts/`. **Session:** courts-2.
**Merge request:** `courts-2` (raised again 30 October evening after the integrator's refusal of 18:44).

## Done

- One source (rulings 126, 127): the MCP's courts corpus as `support/mcpsource` landed it, 5,611 records,
  each file by hash. Nothing fetched; `qv4-courts-capture` retired; the old capture tables gone; the old
  listing read only for the gap report.
- Recognised by shape before any reader, measured on every record (11 profiles): case pages 2,686; NZSC
  1,803; NZCA 342; NZHC civil 147, criminal 32; other courts 6; media releases 287; submissions 166;
  transcripts 83; synopses 37; scanned 4; 13 caught by the pull; 5 set aside. One `judgment_pdf` in six
  is not a judgment.
- The case page read (court, name, citation, case numbers, dates, judges, summary, result, links), joined
  to its PDFs by url and `case_slug`: `courts.cases`, `courts.case_links`, `courts.documents` (every
  record with its outcome: read, waiting on a reader, set aside, caught).
- The text reader (`model_read.py`): Flash-Next through `support.modelclient`, one reading per document,
  stamped and stored by hash, replayed by every load: names with roles, counsel per party, a summary →
  `courts.people` → `pub.court_people` for the links lane. The deterministic fields stay.
- Suppression reaches every name on every document of a citation and its case page, model-read names
  and the case name included.
- A document is its bytes (the refusal of 18:44, `cases_pkey`): a file the corpus holds under several
  records (three pairs on live) is read once, under the plainest url; a case, its links, a judgment, its
  parties, paragraphs and people are emitted once; every sharing record's `documents` row carries the
  reading; `read._once` asserts every key once before the COPY; `check.py` counts the sharing records.
- Full corpus built with this code into a scratch schema (204 s): 5,611 accounted for (text reader 5,589,
  page reader 4, set aside 5, caught 13); judgments 2,329 (parsed 2,224), parties 7,870, cases 2,685,
  links 4,548; 1,061 names withheld under 445 flagged judgments; listing gap 80. Check green, after the
  counsel-role rule learned the 2004–2012 NZSC criminal leave shape ("for Applicant", "for Crown").
- Fast tier green (86.5 s; 50 tests; one xfail until a text-reader reading exists).

## Waiting

- The integrator: profiles, the three jobs, the read pieces queued. No document has a model reading until
  `qv4-courts-read` runs.
- The provider: 80 judgments of the old listing (NZCA 37, NZHC 43; 2025–2026) the corpus lacks (card).

## Carded

`the-mcp-s-courts-corpus-lacks-80-judgments-the-old-listing-names`, `four-courts-files-no-shape-recognises`;
open from courts-1: Waitangi Tribunal and District Court (the corpus has neither), High Court outcomes.

## Next

1. After the first `qv4-courts-read` run: people rows on live, the xfail green; read ten documents'
   summaries and roles against the PDFs.
2. The links lane reads `pub.court_people` (its own card, its session).
