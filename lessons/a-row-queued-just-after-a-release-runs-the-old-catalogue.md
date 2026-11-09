A row queued just after `support.installer release` can be claimed by a worker still holding the old catalogue: wait for "catalogue reloaded" in each box's journal before queueing a job whose catalogue entry the release changed.
area: scheduler, release, deploy, jobs

Why: on 10 November 2026 qv4-courts-pages got its `pieces_command` in b68fb5d, released at 04:57:47 NZDT and queued at once. node2 claimed the row at 04:58:16 with the catalogue it had loaded before the release, which had no pieces command for that job, so the row ran no pieces, recorded no run and finished "ok", with 217 documents still waiting. node2 reloaded the catalogue at 05:04:15 and node1 at 05:06:41. Queued again after both reloads, it listed its pieces.

How to apply: after a release that changes jobs.toml, `journalctl --user -o cat | grep 'catalogue reloaded'` on both boxes (node1 through ssh), and queue the changed jobs only after both lines appear. A pieced row that finishes "ok" with `pieces_total` 0 and no run row is this fault, not "nothing waiting": that outcome's detail reads "nothing waiting".
