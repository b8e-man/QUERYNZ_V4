The fetch gate calls every 5xx "a block or a challenge"; a lane must tell a server's own error (a 5xx with no challenge on the page) from a block, set it aside and go on, and record a polite early stop green when something landed.
area: capture, fetch gate, failed reads, hard limit 6, jobs, checks board
paid-for-by: 2026-10-21, fix-registers-real-estate-authority-1

The Real Estate Authority capture of 20 October had landed 292 PDFs when
one HTTP 500 came back. `fg.looks_challenged` puts 500, 502, 503 and 504
in `CHALLENGE_STATUSES`, so `Fetched.blocked` was set, the lane stopped
the run as a hard-limit-6 block and exited 1, and the board went red for
a good night's work. The fix in the lane: a server-error status whose body
passes `fg.looks_challenged(200, body)` clean is a failed read, rested
after; a challenge behind a 503 still stops. The exit is green on a stop
that landed something. Other lanes that stop on `f.blocked` alone have
the same fault.
