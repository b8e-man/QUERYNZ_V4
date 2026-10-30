# hansard: where it stands

**Date:** 2026-10-31. **Rulings:** 96, 97, 130 (pending: the common rules of 31 October). **Lane:**
`registers/hansard/`. **Session:** hansard-3 (Fable). **Merge request:** `hansard-3` (raised).

## Done

- hansard-1: the old transcripts exported once (137 days, 3,923 sections, 47,243 turns); merged 1a35c33.
- hansard-2: the MCP's index and daily PDFs (1,862 days, texts private); merged 3063cc7.
- hansard-3, the split (profile `hansard-day` v1, `split.py`, no model): two layouts (final 1,827 days, draft 35);
  every one of 1,862 days split, 0 set aside; 38,472 sections, 613,481 turns, 538,115 with a member from the old
  roster. Proved on the 137 days both hold: member turns more than the old lists on 129 days (53,690 against
  40,098: the old lists skip an oral question's question line and most debate speakers, e.g. 2 of 20 on a third
  reading), fewer on the 8 urgency sittings whose later days the MCP lacks; sections equal on 16 (the old made a row
  per parent heading). `pub.hansard_speeches` carries the split's turns for the 1,725 MCP-only days (the spec's
  waiting item closes); `pub.hansard_day_sections` new.
- The names reader (`model_read.py`): Flash-Next through the model client, 40,000 characters a piece (measured
  4.0 to 4.8 characters a token; a 39,199-character piece used 9,717 prompt tokens of 16,384), one piece per
  section, cut at turns, paragraphs, lines; pieces stored at page p, joined at page 1; truncated answers salvaged,
  unusable ones stored after two attempts. `people` → `pub.hansard_people`; `readings` one per piece.
- `check.py`: the split and reader figures (counted; fails on a reading under another profile version, an
  unaccounted day, a turn without its section); green on the whole corpus in `scratch_hansard_3_full` (65 s build).
- Fast tier `registers/hansard` green in 92 s, 55 tests; the sample's five days read once (125 pieces, 1,697 names:
  person 594, body 489, other 275, agency 256, company 83; 0 unusable, 0 cut); a day alone on the server reads in 2
  to 5 minutes, shared with other lanes' pieces in 25 to 43.
- Lesson `a-split-rule-is-proved-against-printed-lines-not-the-old-estate-s-derived-counts`.

## For the integrator

- Append `hansard-day` v1 from `profile-proposed.jsonl`; queue `qv4-hansard-read` (block in the merge request);
  `qv4-hansard-load` unchanged. `pub.hansard_people` and `pub.hansard_day_sections` go on the board in the merge after.
- Arthur's to drop when done: `querynz_v4_sample.scratch_hansard_3_full` (+ `_private`).

## Next

- After the first `qv4-hansard-read` run: people rows on live; read ten pieces' names against the PDF text.
- 3,176 sections (8.3%) have no speaker turn (cover lines, 678,052 chars in all) yet cost a piece each; a rule
  version that skips them saves ~7% of the 45,237 pieces. Not changed here: it would re-key the stored readings.
- The links lane reads `pub.hansard_people` (its own session; ruling 123).
