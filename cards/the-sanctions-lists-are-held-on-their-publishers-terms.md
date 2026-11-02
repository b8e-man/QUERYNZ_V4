# The sanctions lists are held on their publishers' terms; nothing is landed
kind: blocker
state: closed
use-case: 13 beneficial ownership and AML; step 5.3
session: sanctions-1
opened: 2026-10-21
closed: 2026-11-02

`registers/sanctions` is built (capture, three readings, load, publish, check, 20 fast tests and 2 live ones, with a 12-way mutant
check) and lands nothing. Each publisher's terms bar the capture as briefed (`position/sanctions-lists.md`):
MFAT's terms of use bar automated access (the copy is CC BY 4.0, so a hand download is allowed); the UN's allow
personal, non-commercial copies with no compiling; Police's allow saving for non-commercial private purposes only.
Read in memory on 21 October 2026 and kept nowhere: the UN XML reconciles 1,010 of 1,010; the Police workbook
826 items as 811 listings, 3 set aside, 12 counted. Police's 1373 page says 22 current designations; its workbook
and its own table hold 21 (check.py will be red on that until Police correct one or the other). MFAT's reader is
written from a published description of the workbook and is unverified until a real file is landed.

Closes when Arthur's three queue items are answered
(`whether-to-ask-the-un-…`, `whether-to-ask-police-…`, `whether-to-ask-mfat-…`) or MFAT's workbook is landed by
hand: add the `authorised:` lines (or run `capture.py --file`), fill sample.list, put the two jobs in the catalogue.

**Closed 2 November 2026 by ruling 132** (Arthur: "copy: ... the sanctions lists"). The position
(`docs/legal/positions/sanctions-lists.md`) carries `authorised:` for all three lists; the three queue items are
closed on the ruling. The capture asks each list weekly by its own record, one request at a time, 10 s apart,
off-peak, nothing fetched twice; a challenge or bot wall is a failed read of that list and the next is asked.
`qv4-sanctions-capture` (141) and `qv4-sanctions-load` (142) are in the catalogue; sample.list names what landed.
