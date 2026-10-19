# windowed-3: a year of the Authority's database cut short is listed again
branch: session/windowed (pushed; ce97ca5)
session: windowed (session 2)
raised: 2026-10-19
claims: registers/real_estate_authority/capture.py (`complete_years`, `Tables.listed_years`), its tests; docs/status/windowed.md (3cd0166, ce97ca5)

The first capture (by day on Arthur's word, 19 October 08:36 to 13:06)
lost 2016's listing at page 2 of 22 (a connection reset). Page 1 was
recorded, so `listed_years` counted 2016 as listed and no later run would
list its other 203 decisions. Now a year counts as listed only when every
page of it has been read; a year cut short is listed again from page one.
Checked on `querynz_v4`: the next run lists 2016, 2025, 2026.

Fast tier: `registers/real_estate_authority` 19 passed (two new tests).
Merge before 22:30 if you can: tonight's scheduled run then fetches 2016.
Otherwise the first run after the merge does it; nothing is lost meanwhile
unless 2016's Committee decisions leave in the gap.
Lesson: nothing new (the old "a backwalk reports how much is LEFT" covers it).

## Result (integrator, 2026-10-19 14:58)

Merged into main as ae1481b, before tonight's 23:00 run, which lists 2016
again. Fast tier green (merged main first; generated records unchanged).

The first by-day capture ended 12:36 (Authority) and 13:06 (Tribunal):
Tribunal 6 months equal, 3,578 held, 30 of the 2024-03 month short; Authority
1,226 of 3,084 held across 17 years. Both continue on the queue's clock.
