# Contract: the register row

**Fixes:** what every published row carries. **Test:**
`support/rowcontract/tests/`. **Taken from:** the old donation rows, which
were renumbered nightly and broke every citation, and the company views
that dated every ending to the import day.

1. **A stable key**, the same across re-reads, amendments and nightly
   rebuilds. A copied register's key is the source's own identifier for the
   row; a built register's key is the document's hash plus the place in it.
2. **The document's hash, the page and the place** it came from.
3. **The dates as filed.** An ended role carries the day it ended as the
   file states it, never the load day (contract: dates). `loaded_at` is
   when the row was written and is never a date of anything.
4. **The reader, and the document profile and version** the reading ran
   from, so the row is explicable after the profile moves on.
5. **Whether it was read from text or from pixels.** A figure read from
   pixels is weaker evidence and every surface says so.
6. **A person's home address is not a column.** It lives in the lane's
   `_private` schema, keyed by the row's key, and no published table or
   export carries it (hard limit 15). A suppressed name is suppressed on
   every surface; the row and the money stay (hard limit 16).
7. **Rows are rebuilt from documents, never edited.** A wrong row is fixed
   by fixing the reading or adding a correction.
8. `support.rowcontract.validate` returns the problems as plain lines; a
   lane's tests run it on every row of the lane's sample.
