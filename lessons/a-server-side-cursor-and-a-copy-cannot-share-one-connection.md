A server-side cursor and a COPY cannot share one psycopg connection: the next batch fetch waits behind the open COPY and the process hangs silently at 0% CPU; read through a second connection.
area: links, lanes, any bulk read-transform-write over the published tables
paid-for-by: 2026-10-20, links session, step 4.2

`links.rows.gather` read `pub.directors` through a named cursor (itersize
20,000) and wrote through `cursor.copy()` on the same connection. The first
batch went in; the fetch of the second blocked, because the connection was
inside a COPY. `pg_stat_activity` showed no active statement, the log was
empty (stdout buffered), and the process sat for eight minutes. Two
connections to the same database, one reading and one writing, finish the
2.75 M rows in three minutes. Run bulk scripts with `python -u` so the log
shows where they are.
