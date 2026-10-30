# courts: where it stands

**Date:** 2026-10-31. **Step:** 5.4 items 2 and 3, `registers/courts/`. **Session:** fix-registers-courts-1 (fix).
**Merge request:** `fix-registers-courts-1` (branch `fix/registers-courts-1`).

## Done

- Live since the merge of courts-2 (30 October 19:40): `qv4-courts-read` read 5,587 of 5,589 pieces in its first
  night (19:43–03:52); `qv4-courts-pages` read the scanned pages; the 04:40 `qv4-courts-load` built its staging
  schema and refused to publish on 76 check failures.
- The refusal's cause, measured: the keep rule under a suppression (hard limit 16) ran as Python in the load and as
  SQL in the check and the lever, and the Crown pattern held `\b`, a word boundary to Python and a backspace to
  Postgres. One rule now: `model_read.KEPT_ROLES` + `caption.CROWN` (dialect-neutral), `kept_under_suppression`
  for the load, `kept_sql` for the check and the lever, pattern inlined. Whole corpus through this branch: old SQL
  flagged 75 of 6,797 names on documents a suppression reaches, every one an Attorney-/Solicitor-General shape; the
  one rule flags 0; check failures 0.
- The two failed pieces: the model's answer hit the 4,096-token cap (about 95 entries, JSON cut mid-item). Salvaged
  now to the complete entries, stamped `truncated`; a name the model repeats is listed once; an answer with no
  object is asked once more on half the excerpt, then stored `unusable` so the piece ends done and the next load
  sets the record aside at stage `read`. No piece loops.
- Court code in one spelling (`NZEmpC`, not `NZEMPC`); a transcript's cover sheet (court line with the case number
  beside it, no citation) now names its court: the 18 `?` were 17 hearing transcripts of 2008–2018 (98–383 pages)
  recognised as NZSC judgments by shape, and one 2004 leave decision; all unparsed, Supreme Court by the court line.
- Six lane tests green against the real store: the scanned record is read from pixels once its page readings exist
  (profile by shape, caption partial: the pixel text prints name over role with no BETWEEN); the suppression tests
  use the one rule; a new test holds Python and Postgres to the same answer on every sample name and the Crown's shapes.
- Fast tier green (82 s; 60 s target missed, recorded).

## Waiting

- The integrator: merge, rerun `qv4-courts-load`; expect the check green and `pub.court_people` filled. The two
  pieces re-queued read as truncated readings.
- The 31 October pull grew the corpus to 5,941 records: 179 set aside at recognise, 150 waiting on the text reader,
  12 on the page reader (measured in this session's scratch build; not this fix's).

## Next

1. Read ten documents' summaries and roles against the PDFs (courts-2's item 1, still open).
2. The transcripts the shape recogniser files as NZSC judgments (17 of them): a profile question, carded by whoever
   next touches the profiles.
