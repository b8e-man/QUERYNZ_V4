# courts: where it stands

**Date:** 2026-11-03. **Step:** 5.4 item 1 (ruling 130) and ruling 140's own capture, `registers/courts/`.

## Done

- The text reader reads whole documents in pieces by each profile's split rule (`pieces.py`; budget 34,000
  characters); `courts.documents.pieces` holds the count and the check fails a document read without one.
- Profiles added 30 October to 3 November: ERA determinations, HRRT and other tribunal decisions, District Court
  ACC appeals, hearing transcripts, the Māori Land Court and Māori Appellate Court (`courts-maori-court-judgment`).
- Own capture (ruling 140): JDO, the Ministry's decisions finder (22 bodies) and the ERA, nightly 22:00 NZDT, 5 s
  floor; the MCP's file wins by hash.
- 3 November: the counsel-role check's two grammar misses mended; two court-printed exceptions counted apart.
- 3 November (Arthur: any identifying information), tranche 1: `identifiers.py` finds the details with a fixed
  shape (emails, phones, PO boxes, street addresses, ages, dates of birth, company numbers, NZBNs, IRD, licence and
  plate numbers) in the text the lane holds, no model, into `courts_private.identifiers`; never published; the
  check fails an identifier column in a view or reading table, or a view on the private schema.

## Waiting

- Set aside, Arthur's call: 15 unsplittable documents (a page fallback would read them; no default).
- Weathertight Homes Tribunal decisions have no profile (15 set aside, 12 taken for submissions in the trial).

## Next

1. The Weathertight profile, then each finder body's as the backfill lands it.
2. Identifying information, the model's half (occupations, employers, firms, relationships, places of residence,
   addresses printed without a fixed shape, per person): `docs/research/what-each-profile-extracts.md`.
