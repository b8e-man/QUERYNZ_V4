Before keying or joining on a published identifier column, count its shapes: the GETS supplier file's "Supplier NZBN" holds no valid NZBN at all, its numbers saved in spreadsheet exponent form with the digits gone.
area: reading CSV, keys, NZBN, supplier, joins, procurement, csv encodings, mutant checks
paid-for-by: 2026-10-21, tenders-1 session, step 6.2

The plan, the old estate's notes and the ministry's own catalogue all call
the award notices "keyed on official business number". Counting the
column's shapes before writing the reader (digits to 9, letters to a)
showed `9.99999a+99` (12,694 of 31,265: `9.42904E+12`, six significant
digits, the NZBN unrecoverable), empty, `NULL`, six to nine digits, free
text, and no 13-digit value. The old estate loaded the column as text and
never looked. Keep such a column as published, fill the key only for a
valid value, and name the shape beside it so a later join can see why it
is empty. Two more from the same files: they mix encodings within one file,
so decode field by field (UTF-8, else Windows-1252, else Latin-1, counted);
and a mutant that swaps Windows-1252 for Latin-1 passes on `é`, which is
the same byte in both: test with a byte where they differ (0x96, the en
dash).
