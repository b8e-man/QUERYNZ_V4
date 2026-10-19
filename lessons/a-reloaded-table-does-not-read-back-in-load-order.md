A table loaded by COPY does not read back in the order it was loaded (PostgreSQL 18): compare a restored table with its source as a multiset of rows, never as one ordered hash.
area: off-site copy, restores, any check that a reloaded table equals its source
paid-for-by: 2026-10-19, offsite session 2, track B

The first restore rehearsal hashed each table's `COPY ... TO STDOUT` text
on the way out and expected the restored table to give the same hash,
assuming a freshly loaded heap is scanned in load order. 59 of 270 tables
failed, every one with the same rows in another order: a plain `CREATE
TABLE (LIKE ...)` loaded by one COPY from the same bytes read back
differently and took 38 pages for 25 pages of rows (the bulk insert extends
the file several pages at a time and places rows out of order). The check
is now two halves: each object's text has the sha256 recorded at the
source, and the table read back has the same row count and the same sum of
per-row hashes (`support.offsite.restore.Multiset`). The objects were never
wrong; the check was.
