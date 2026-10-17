# Contract: dates

**Fixes:** how a date is read from a filing, and which date a row carries.
**Test:** `keys/tests/test_addresses_numbers_dates.py` (the reading) and
`support/rowcontract/tests/` (the row rule). **Taken from:** the old
`party_names.year_from` and the fault that dated every ended company role
to the import day.

1. **Read day first**, in every shape the forms arrive in: `07/09/2026`,
   `21/1/26`, `10 Mar 2026`, `2026-09-07`. A date that is not a real day
   (`45/08/2014`, `08/15/2023`) is None, never a guess.
2. **A year read from pixels is checked against the Commission's own file
   name.** When the day and month agree and the year does not, the file
   name's year wins and the basis says `source_file (read year corrected)`.
   A year in the far future is not a date. A row with no year is shown with
   a flag, never windowed away: basis `undated`.
3. **An ended role carries the day it ended as the file states it,** never
   the day the file was imported. A row's `ended_on` must come from a
   document field; a lane that cannot read one leaves it empty and says so
   in its catch log. The row contract refuses an `ended_on` equal to the
   load day unless the document states that day.
4. **Two dates where the source gives two:** the Commission's table of
   large declarations leads with the day it received the declaration, weeks
   after the party received the money. A row keeps both, named
   (`received_on`, `given_on`); a product shows both.
5. **Dates are stored as dates** (ISO `YYYY-MM-DD`), never as text, and a
   date read from pixels is marked as such through the row's `read_from`.
