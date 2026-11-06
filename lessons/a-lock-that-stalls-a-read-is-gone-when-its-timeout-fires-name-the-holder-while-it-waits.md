A lock that stalls a read is gone by the time its timeout fires: name the holder while the read still waits, and try again rather than lose the day.
area: published_site, scheduler, postgres
paid-for-by: 2026-11-07, the site build's 08:00 read on 4, 5 and 6 November

The site build's read, normally 4 s, waited 120 s three mornings running
and was cancelled; the comparison had no rebuilt side those days. The
journal said only "statement timeout", the server log needs sudo, and by
the time anyone looked the blocker had finished. The run record could
only suggest a cause (the links build ran beside it each day), not prove
one. A watcher thread asking `pg_blocking_pids` every few seconds during
the read catches the holder while it holds; a `lock_timeout` below the
statement limit turns a wait into a named, retryable error.
