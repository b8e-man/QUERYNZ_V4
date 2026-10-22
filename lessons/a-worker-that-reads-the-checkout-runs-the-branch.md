A worker that reads its catalogue and code from the main checkout's working tree runs whatever branch that checkout is on, so an integrate branch's new jobs run live the moment the catalogue reloads, before the gate.
area: scheduler, worker, the merge gate, integrate branches, jobs.toml
paid-for-by: 2026-10-22, procurement-1, the integrator

Found 2026-10-22 at the procurement-1 merge: `qv4-worker@node2` has the main
checkout as its working directory and re-reads `support/scheduler/jobs.toml`
every few minutes; `queue.slot_for` makes a job new to the catalogue due at
once (yesterday's slot was never served). The three procurement jobs and,
that morning, the three settlements jobs ran during their branches' fast
tier. Card
`the-scheduler-s-worker-runs-the-main-checkout-s-working-tree-so-an-integrate-branch-s-jobs-ran-live-before-the-gate`.
Interim: stop the idle worker before checking out an integrate branch and
start it after the push; the fix is a release copy for the worker and
"next slot" for a new job.
