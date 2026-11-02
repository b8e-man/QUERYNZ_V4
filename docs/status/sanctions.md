# sanctions: where the step 5.3 lanes stand

Ruling 132 (2 November 2026) copies the three sanctions lists. Session for it: this branch.

## Done

- `registers/sanctions`: the hold lifted (`authorised:` for all three in
  `docs/legal/positions/sanctions-lists.md`); the card and the three queue items closed on the ruling.
- Capture: weekly per list by its own record, one request at a time, 10 s apart, off-peak, nothing fetched twice; a
  block or challenge is a failed read of that list and the next is asked; the UN XML follows its one redirect.
- First capture 2 November 22:01 NZDT, into the sample database (`scratch_sanctions_132`): 10 requests, 10 landed,
  none challenged. Read into `staging_sanctions_132`: MFAT 1,918 listings (9 September), UN 1,007 (31 October),
  Police 494 current + 317 ended (21 October), 3 set aside. Reading and views clean.
- MFAT profile v2 from the real file: its Total row tallies a column (170 under Associates/Relatives), not listings.
- The real files put passport numbers inside 5 published values (aliases, positions, a birth note); the reader now
  cuts any identity-document phrase from every value; a slow test on the landed files holds it.
- Jobs: `qv4-sanctions-capture` (141, 23:30 NZDT), `qv4-sanctions-load` (142, 06:35 NZDT).
- `limited_partnerships` and `building_practitioners`: unchanged here.

## Red, correctly

- check.py: Police's 1373 page says 22 current designations; its workbook holds 21 (as on 21 October).

## Next (integrator)

- Merge; append MFAT profile v2 to the registry; let the capture job land the lists live (the sample capture is not
  in `sanctions.capture_documents` on querynz_v4); the load publishes on a clean reading.
- Template 13's `sanctions-lists` rule still says no list is held: its own session.
