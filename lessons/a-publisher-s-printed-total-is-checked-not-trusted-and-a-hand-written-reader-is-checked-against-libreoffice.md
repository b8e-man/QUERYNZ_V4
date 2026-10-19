A release that disagrees with its own printed total is the publisher's slip only once the reader is proven: check a hand-written workbook reader cell for cell against LibreOffice, then report each printed total that differs from its rows.
area: reading workbooks, expenses, xlsx, xls, outside checks
paid-for-by: 2026-10-20, interests-expenses session, step 4.1

The estate has no spreadsheet package, so the expenses lane reads xlsx
(zip of XML) and xls (BIFF8 in OLE2) with the standard library
(`registers/expenses/sheet.py`, `biff.py`). Before any figure was trusted,
both readers were compared with `soffice --convert-to csv` on all 100 held
workbooks: 64,137 cells equal, 16 different, and those 16 were error cells
LibreOffice recalculates (the file's cached `#REF!` against its `#NAME?`).
Only then were the publishers' own totals read as checks: 3,865 of 3,865
members' lines and 2,341 of 2,364 ministers' lines add to their own
totals; the rest, and nine grand totals, are the publishers' arithmetic
(a grand total that leaves out a whole party's column). Without the cell
comparison each of those would have been a question about the reader.
Two more traps from the same files: a catalogue's label for a workbook can
name another quarter than the workbook's own title (read the title), and a
capture job that names files after the publisher's file name loses a
quarter when the publisher reuses the name.
