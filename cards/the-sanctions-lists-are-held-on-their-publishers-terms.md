# The sanctions lists are held on their publishers' terms; nothing is landed
kind: blocker
state: open
use-case: 13 beneficial ownership and AML; step 5.3
session: sanctions-1
opened: 2026-10-21

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
