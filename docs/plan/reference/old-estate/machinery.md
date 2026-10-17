### Machinery

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Scheduler parts | `ops/fleet/`, `config/job_types.yaml` | Nothing runs it on a clock; queue depth unmeasured | Extend in step 2 |
| Work queue with leases | `ops/extract_queue.py` | Specific to press extraction | Take the pattern |
| Re-read orchestrator | `ops/era_cutover.py` | Jobs it pauses do not restart themselves | Take the pattern for the re-read job type |
| Old checks board | `tests/test_invariants.py`, run daily by the `v3-audit` job | 11 of 73 red on 10 October. None of fifty checks asserted the value of an answer a user sees. It was once dead for days while every row read nominal. Its only watcher is the sweep job | Rebuild in `checks/`; the new board alarms if it has not run |
| Old card board | `ops/board.py` | None documented | Replaced by the generated board |
| Job manifest | `ops/systemd/MANIFEST.json`, checked by `ops/units_manifest.py` | Jobs were once installed nowhere, or on one box only | Generated in the new estate |
| Hooks | `.claude/hooks/denylist.py`, `session_scope.py`, switched on in `.claude/settings.json` | The scope hook reads an old path for its scope and allows everything without it | Port, do not copy (step 1.1) |
| Lessons tools | `ops/lessons_for.py`, `ops/lessons_index.py` | Retrieval recall measured at 5 of 8. The search prints whole sections, up to 160 KB at a time | Take the one-line index. Write a new search over it and the new lesson files (step 1b) |
| Database, standby, floating address | Runbook in `docs/runbooks/` | Takeover by hand; one drill | Track A |
| Off-site backup | The `offsite-push` job | 368 GB nightly; restore rehearsed to 90% | Track B |
| Citation resolver | In `data-layer/pi` | Donation citations pointed at row numbers that changed nightly | Take, on stable keys |
| Rate limit | In `data-layer/query` | A courtesy bar, not a control | Not enough for strangers |

