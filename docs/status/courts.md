# courts: where it stands

**Date:** 2026-10-31. **Step:** 5.4 item 1 (ruling 130), `registers/courts/`. **Session:** fix-registers-courts-2 (fix).
**Merge request:** `fix-registers-courts-2` (branch `fix/registers-courts-2`).

## Done

- The text reader reads whole documents, never an excerpt (ruling 130). Each courts profile carries the reader's
  budget (34,000 characters: 16,384 tokens less the 4,096 answer, at the worst ratio of 3.3 characters a token
  measured on 5,679 calls) and a split rule: whole, paragraphs, numbered, pages (`pieces.py`). A document over the
  budget is read in pieces, one call each, the answers stored as they come (a run stopped at its deadline resumes),
  names joined under the one hash, the summary from the pieces' summaries in one more call. The rule that cannot
  split a document sets it aside at read, named. `courts.documents.pieces` holds the count; the check prints the
  documents by pieces needed and fails a document read without one.
- Whole corpus through the branch (6,411 records): 6,360 waiting on the text reader; 1,067 over the budget;
  9,527 pieces (1: 5,293; 2: 466; 3–5: 426; 6–10: 124; over 10: 51; the longest a 57-piece transcript); 15 cannot
  be split (14 Authority determinations and one judgment whose text layer numbers no paragraph).
- Two kinds of 30–31 October: `courts-era-determination` (292, determinations.era.govt.nz; 289 were taken for
  submissions by "Submissions received") and, from justice.govt.nz/assets/Documents/Decisions, `courts-hrrt-decision`
  (389), `courts-tribunal-decision` (71, nine bodies by their citation codes), `courts-nzdc-judgment` (10 ACC
  appeals). Caption grammar reads their labels, dates and court codes; suppression banners of both found and
  flagged (Authority 51 of 292, Tribunal 129 of 389).
- Transcripts filed elsewhere: 18 as NZSC judgments (cover sheet with Appearances and speakers' lines) and 21 of
  2004–2008 as submissions (two-column layout, the speaker in a left column), now `courts-hearing-transcript`.
- Profile versions bumped in `profile-proposed.jsonl` (14 lines) so every document reads again; old readings stay.
- Sample: 9 records added for the new kinds, two for the transcripts, one unsplittable determination.

## Waiting

- The integrator: merge, append the 14 proposed profile lines to `support/profiles/profiles.jsonl`, reload,
  re-queue `qv4-courts-read` from `--pieces` (about 10,600 model calls); figures and steps in the merge request.
- Set aside, Arthur's call: the 15 unsplittable documents (a page fallback would read them; no default).

## Next

1. Read ten documents' summaries and roles against the PDFs (courts-2's item 1, still open).
2. One Decisions-folder letter-shaped decision is taken for a submission and set aside; the three set aside at
   recognise from justice.govt.nz and the one from employmentcourt.govt.nz carry their reason in the check.
