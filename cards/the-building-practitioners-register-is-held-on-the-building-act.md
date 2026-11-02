# The licensed building practitioners register is held on the Building Act's search purposes
kind: blocker
state: closed
use-case: 6 insurance, 7 construction and phoenix, 12 property developer; step 5.3
session: sanctions-1
opened: 2026-10-21
closed: 2026-11-02

Building Act 2004, s 307: the register may be searched only for a purpose s 299 names; s 308: any other search for
personal information is an interference with privacy under the Privacy Act 2020. Copying the register for our
products is not such a purpose, so `registers/building_practitioners` asks the register nothing, has no reading of
it (its shape has not been seen, because looking would be a search), and `pub.building_practitioners` is empty.
The Board's published decisions are captured and read (four of about eighty list pages so far; 80 of 80 decisions
read, 1,600 stated). Closes on Arthur's queue item `whether-the-building-practitioners-register-may-be-copied-at-all`:
if a one-practitioner check is lawful, build it as an on-request lookup; if not, the templates say "licence status not
held".

Closed on ruling 132 (Arthur, 2 November 2026: "copy: Building practitioners register"). The position carries
`authorised: register 2026-11-02 ruling 132 …`; the queue item is closed on the ruling. `register.py` copies the
register through its own public search: 26 searches a week (seven licence classes, nineteen areas of practice; a
search with no criterion did not answer in 60 s and is never asked), then each listed practitioner's page once,
again after 90 days, 5 s apart, off-peak. Each page gives the practitioner number, the names, the date a class was
first granted, the region and the town; the postcode, email and telephones on it are never read. The town is
published whole with `area_names_address` beside it (ruling 102). Proposed job `qv4-building-practitioners-register-capture`
(priority 151); the existing load job reads the register too. What the copy does not reach is on the card
`the-building-practitioners-register-s-sub-tables-and-lapsed-practitioners-are-not-read`.
