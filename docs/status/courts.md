# courts: where it stands

**Date:** 2026-10-21. **Step:** 5.4 items 2 and 3, `registers/courts/`. **Session:** courts-1.
**Merge request:** `courts-1` (raised).

## Done

- Held, by hash, never fetched: the old estate's listing exported once (359 documents, sha256 8285d006…); 353
  files copied by hash (148 courtsofnz judgments, 205 Waitangi Tribunal documents); 6 files gone (3 judgments,
  3 Tribunal reports). No District Court judgment held.
- Research note (`registers/courts/research-legal-documents.md`, for `docs/research/legal-documents.md`) and five
  profiles measured on every held document (`profile-proposed.jsonl`).
- Reading, deterministic, text layer only: 148 judgments parsed, 0 partial, 0 unparsed; 590 parties (166 low,
  27 anonymised, 112 Crown); 19,990 numbered paragraphs indexed; outcomes for 74 of 83 SC/CA.
- Suppression: 60 judgments flagged (banner 49, order in the text 41), 89 names withheld to `courts_private`.
- The lever `suppress.py`: dry run by default, ledger never wiped, no unsuppress; applied again at publish.
- `capture.py` job `qv4-courts-capture` (RSS for cadence, the gone files), refused by the gate until the position
  moves. `check.py` green on the full read and the sample. Tests: caption, mutants (9), capture fakes, lane.

## Waiting

- The integrator: the six edits in card `the-courts-lane-s-edits-outside-its-fence`.
- Arthur: the Ministry of Justice letter (tribunals, Judicial Decisions Online; not these hosts).

## Carded

`waitangi-tribunal-reports-are-held-and-not-read`, `district-court-judgments-are-not-captured`,
`high-court-outcomes-are-not-read`.

## Next

1. After the merge and the first capture run: the three gone judgments and the RSS cadence land; re-run the check.
2. The District Court listing (card), then its profile.
