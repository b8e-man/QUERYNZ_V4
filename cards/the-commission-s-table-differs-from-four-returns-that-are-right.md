# The Commission's table differs from four returns that are right
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-20

The outside check (`python -m registers.party_returns.commission`)
compares each current return's declared total with the "Total party
donations" the Commission prints for that party and year on "Party
donations and loans by year", 2017 on, tied by the files the listing links.
On the live load of 20 October: 117 party-years equal to the cent, 5
differ, loans 0 differ. Four of the five are the Commission's table, not
the lane; each page was read by eye:

- **Green Party 2021**
  (`e5c7f64c836f3a8f264446cee0f76797ca6dd5f7b314d0f10474011594682c9a`):
  the return prints $403,787.55; the table says $403,787.00.
- **NZ Outdoors Party 2020**
  (`62c91cb7400d5db5b34088862780a6c8d571b62e369ad4e2bec6a3fd8a9f2318`):
  the return prints $7,220.00 (Part G and total); the table says $7,200.00.
- **HeartlandNZ 2021**
  (`a1b3504e09852f7efa19074348ff1d46dce3adaa81c618978cc999d2bb76d7cc`,
  the amended return): it prints $2,870.00; the table says NIL, which is
  the original's figure.
- **New Conservatives 2024**
  (`e812a037cdda2c152b87b31224bb166ac78edf14734579731831e7c2ab1426db`,
  the amended return): the A to G total is $8,898.63; the table says
  $9,188.63, which adds the $290.00 the form prints apart as
  "Total Non-Monetary Party Donations". Another basis, not a slip.

The fifth, Labour 2017, is the lane's: card
`labour-2017-the-page-reader-drops-a-handwritten-correction`.

Not tied, and so not compared: 11 Commission rows whose returns are set
aside at the declaration; NZ Outdoors & Freedom 2023, whose file name
(`Party-Donations-and-Loans-Return-FILLABLE-v2.pdf`) the old folder holds
under more than one set of bytes (our row equals its $290.00 anyway); and
two returns the table does not list (National 2022's second copy, queued
for Arthur; one NZ Outdoors & Freedom 2023 file). Nothing to fix in the
lane; accept onto the known-limits page at the checkpoint.
