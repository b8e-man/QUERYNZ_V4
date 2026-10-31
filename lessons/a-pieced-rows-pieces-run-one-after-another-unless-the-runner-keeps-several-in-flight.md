A cap on ROWS of a job type is not a cap on requests in flight: a pieced row ran its pieces one after another, so four rows allowed by `concurrency` gave a 16-slot server one request at a time; measure the server's own busy count.
area: scheduler, worker, pieces, concurrency, model servers, bulk ingest
paid-for-by: 2026-10-31, the integrator's measurement on qv4-courts-read row 936 (9 pieces a minute, num_requests_running 1; eight hand streams 155 a minute); fixed in fix-support-scheduler-6

`Worker.eligible` counted rows of a job type against `concurrency`, and the
runner of one row took its pieces serially. With one row queued by hand the
server saw one request at a time whatever the figure said; the recorded
piece seconds equalled the wall time per piece, so the loss was the serial
order, not the worker's overhead (a child costs under 0.2 s to start). The
fix keeps N pieces in flight per row, N = min(concurrency, the profile's
measured `streams` less the other rows' pieces), and the profile states the
streams it is worth keeping open (eight; sixteen was slower). The general
rule: when a job's throughput is a fraction of a server's, read the
server's own busy count before touching the scheduler's figures, and make
every cap name what it counts (rows, pieces, requests).
