A raised memory figure the box cannot hold is recorded, never applied: placement skips a job whose figure exceeds the free memory without a word, so an applied over-budget raise would leave its next row queued for ever.
area: scheduler, worker, memory, placement, ruling 115
paid-for-by: 2026-10-28, fix-support-scheduler-1

`Worker.eligible` divides the free memory by the job's working figure; a
figure above the box's budget (its memory less `memory_reserve_gb`) gives
zero copies, so the row is never claimed, never fails and never alarms, and
the timetable then queues nothing new behind it (`enqueue_due` waits while
an instance is queued). So `queue.raise_memory` writes an over-budget raise
with `applied = false`: the measurement is kept and listed by `memory`, the
working figure stays where it was, and the row stays failed and alarmed
with the note. The third raise for one first row is the other way round:
it fits, so it is applied (the next timetabled run starts from it) and only
the re-run is refused. Tested in test_memory_raise_worker.py; the mutant
that applies every raise fails the budget test.
