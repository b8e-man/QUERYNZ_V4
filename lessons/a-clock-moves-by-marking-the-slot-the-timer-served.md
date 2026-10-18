When a job's clock moves from a systemd timer into the queue, mark the slot due now as already served before the worker sees the catalogue; otherwise the queue runs today's slot again the moment it learns the job.
area: scheduler, timetable, installer, jobs
paid-for-by: 18 October 2026, the four founding timers moved into the catalogue

The queue's `enqueue_due` treats a job with no `last_slot` as owed its latest slot (the behaviour a `Persistent=true` timer has), so a job added to the catalogue with a daily time runs at once. That is right for a new job and wrong for one a timer served an hour ago: the board, the full tier and the off-site dump would each have run twice on 18 October. The installer's `superseded` step therefore calls `queue.handover(job)`, which writes the slot due now as `last_slot` (never moving an existing clock back), and does so BEFORE the worker is restarted on the new catalogue. Order matters: handover, then the worker. Hand runs afterwards are ruling 56's.
