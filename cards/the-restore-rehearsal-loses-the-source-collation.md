# The restore rehearsal creates every database in C.UTF-8, so a check the source holds refuses its own rows
kind: blocker
state: closed
use-case: track B, the off-site copy's outside check (`python -m support.offsite restore`)
session: fix-support-offsite-1
opened: 2026-10-23
closed: 2026-10-23

The rehearsal of 22 October 13:00 (copy 20261021T210010) restored
extractions, incoming_news and nzbn_canonical equal, then failed after
6,779 s loading `querynz_v4` `links.links`: `CheckViolation ...
"links_pair_order"` (CHECK (row_a < row_b)). The scratch server ran
`initdb --locale=C.UTF-8` and each database was created from template0 with
ENCODING only, so every restored database collated as C.UTF-8. The live
databases are en_NZ.UTF-8 (libc), where the check was validated; under "C"
three of 2,815,766 live rows compare the other way. Pre-data creates the
CHECK before the rows, so COPY refused them.

The scheduled run of 19 October 10:33 failed in 6 s for another reason:
`DROP DATABASE "extractions"`: ObjectInUse, 1 other session. A hand
rehearsal's scratch server (same unit, port and folder) had been up for 13
minutes with a session on that database. The hand bucket restore of 19
October 19:40 to 21:30 was EQUAL (querynz_v4 35/35); links.links did not
yet hold a row that "C" orders the other way (the one dated is from 21
October).

Closed 2026-10-23 by fix-support-offsite-1. The copy records each
database's encoding, locale provider, collation, ctype (and ICU or builtin
locale) from pg_database in the manifest (`databases.<db>.locale`). The
restore reads it back; the scratch server's initdb and each CREATE DATABASE
(TEMPLATE template0, ENCODING, LOCALE_PROVIDER, LC_COLLATE, LC_CTYPE) use
it. A manifest without it, every copy in the bucket today, takes the live
server's settings read at restore time; the record says which under
`databases.<db>.locale.from` ("manifest" or "live server") and
`server_locale`. Tests: `support/offsite/tests/test_locale.py` (fake
manifest and fake runner). Live proof in the session's scratch folder:
the three live key pairs under the same CHECK load 3 of 3 in a database
the new code made in en_NZ.UTF-8, and raise CheckViolation
links_pair_order in one made in C.UTF-8.

Not fixed here: two rehearsals still share one scratch server (the 19
October failure). A lock like the copy's would refuse the second.
