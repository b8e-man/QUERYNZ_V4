owns: schema `scheduler` (`workers`, `queue`, `pieces`, `cards`, `swaps`, `runs`, `timetable`); `<live>/scheduler/` (the run journal, the server logs, `rereads.jsonl`); `jobs.toml` and `profiles.toml`; the unit `qv4-worker@`
reads: the box (rocm-smi, /proc, the programs); the document store and the reader store for a re-read; `pub.party_return_totals` to compare a re-read; the model profiles' weights under the models folder
publishes: nothing in `pub`; `<live>/checks/scheduler.json` for the checks board (the `qv4-scheduler-report` job); the swap ledger and run records, readable by the session reader
outside check: each loaded card answers with the model its profile names (read back from the card at every load; a wrong answer is a failed swap)
jobs: `qv4-worker@<box>` (standing, one per box); `qv4-scheduler-report` hourly on the queue's own clock; `qv4-reread` and `qv4-reread-pages` on demand in pieces; the rehearsal jobs when queued
