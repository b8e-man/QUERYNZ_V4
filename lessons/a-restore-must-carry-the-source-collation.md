A restore must create each database with the source's collation, ctype and locale provider: a CHECK or index on text holds only under the collation it was validated in, and the same rows can fail it under another.
area: backups, off-site copy, restore, support/offsite, PostgreSQL, initdb, CREATE DATABASE, locale
paid-for-by: 2026-10-23, fix-support-offsite-1 (track B rehearsal of 22 October)

The rehearsal made its scratch server with `initdb --locale=C.UTF-8` and
each database with ENCODING only. The source is en_NZ.UTF-8. Three
databases restored equal; querynz_v4 failed after nearly two hours on
`links.links`, whose `CHECK (row_a < row_b)` three live rows break under
"C". The schema's pre-data section makes the CHECK before the rows, so the
COPY refused rows the source holds. A logical copy (COPY text, pg_dump
--schema-only) does not carry the database's locale: pg_dump writes it
only with --create, which a schema-and-rows restore does not use.

How to apply: record `datcollate`, `datctype`, `datlocprovider` and
`datlocale` from pg_database with the copy, and create the restored
database from template0 with them. Earlier copies fall back to the live
server, and the record says which was used. The same applies to any
scratch database a test or a comparison fills with real rows that have a
text CHECK, a unique index on text or an ORDER BY whose result is compared.
