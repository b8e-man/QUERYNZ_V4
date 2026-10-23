Moving the release copy changes what the next job runs, not the running worker: its own code is in memory, so a release that touches the worker's code says so and the idle worker is restarted.
area: scheduler, worker, installer, release copy, merges
paid-for-by: 2026-10-23, release-copy-1

The worker imports `support/scheduler`, `support/db` and `support/alarm`
once, at start; each job it starts is a new process and reads the copy as
it stands. So a checkout that moves under a running worker leaves two
versions live: the worker's loop on the old commit, its children on the
new one. `python -m support.installer release` diffs the old commit
against the new and reports `worker_restart: owed` when one of those paths
moved (the catalogue files excepted, which reload themselves), or when the
copy is new. A related trap met on the way: `/home/user/querynzv4` is a
prefix of `/home/user/querynzv4-release`, so a unit rewrite matches the
whole `WorkingDirectory=` line, never the bare path.
