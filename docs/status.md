# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages. Written by the founding session during
step 1; by the integrator after.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, present
and proven (the watcher's test alarm, 01:08 on 18 October).

## Done

- Step 0: all but the third machine, which is held with track A.
- 1.1: the fences, launcher, merge gate, record formats, the plan split,
  `CLAUDE.md`, the stop list, the inbox.
- 1.2: the reference copy at `/home/user/qnz3-ref` (commit `29f0412a`,
  remote `live`) with its own Python 3.12 environment matching the live one.
  Run old tests there only with no DSN set: node2's localhost is the primary.
- 1.3: `docs/baseline.md`; node1 down, marked "not measured"; twelve
  differences from the plan, two for Arthur (archive_mode off on the
  promoted primary; a password in the old `querynz-api` unit file).
- 1.6: the watcher (`checks/frozen_product.py`, `checks/board.py`,
  `support/alarm/`, `support/jobrun/`); `qv4-checks-board` 07:30 daily and
  `qv4-checks-heartbeat` 09:00/21:00 installed on node2; first run green;
  listing of 57,765 staged files written; test alarm sent. node1 gets the
  same files from step 2's installer.
- 1.7: `reference/` (old lessons, rulebook, cards, use cases, rulings;
  read-only) and `support/profiles/profiles.jsonl`. The corrections quote
  donor street addresses and stay outside git at
  `/home/user/querynzv4-work/live/reference/corrections.jsonl` until 1.10.
- 1.8: `support/db/` (the schema plan: pub, links, 16 lanes each with a
  `_private` twin, five product shapes, docs, sealed; grants with defaults;
  `bin/db-setup plan|apply|check|scratch`) applied to `querynz_v4` and the
  sample; the one-way test's query half filled from it. `support/offsite/`:
  `qv4-offsite-dump` 03:05 nightly on node2 (pg_dump, gpg, the old bucket
  under `querynz_v4/<stamp>/`, local copies on `/mnt/hdd2/qv4-dumps`); first
  run sent 01:29 on 18 October. `requirements.txt` pins the environment.
- 1.9: eleven contracts, each a document in `docs/contracts/` and a test:
  `keys/` (names, parties, addresses, numbers, dates; 61 old cases carried),
  `support/docstore`, `rowcontract`, `lane`, `reader`, `modelclient`,
  `profiles`, `jobspec`, `links/` (three tables, append-only decisions,
  applied to the sample), `products/templates`.

## Next

1.4 batch 2 after the 06:15 release on 18 October runs green, then batches
3 and 4; 1.5 waits on Arthur (the queue); then 1.10, step 1b, 1.11. When node1 returns, re-measure it into `docs/baseline.md`.

## Half-done

- 1.4: batch 1 stopped and disabled 01:1x on 18 October (`nzme-archive-backfill`,
  `v3-extract`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`,
  `querynz-sweep`, `querynz-embed-backfill`, `querynz-embed-index-ship`; the
  old failure handler sent four alarms for the killed runs, expected). Held
  until the NZME commit lands: `newsscrapers`, `newsscrapers-daily` timers.
  Normal daily change is measured (`docs/baseline.md`, last section;
  `checks/release_compare.py`). Batch 2 waits for a green scheduled release:
  the derive chain, the old apps, `querynz-llm@1`, `querynz-embed`, then
  `v3-audit` last.
- 1.5: BLOCKED. The session's permission mode refuses every write into the
  live old folder. The rehearsed NZME change is the patch at
  `/home/user/querynzv4-work/live/nzme-freeze-commit.patch`; the decision
  queue has the commands.

## Known gaps left on purpose

- The query half of the one-way test (`SCHEMA_OWNER`) is filled in 1.8.
- The hooks know the weights `founding`, `integrator`, `build`; `fix` and
  `question` get their rules in 1b.1. The merge gate is one tier until 1b.7.
- The installer and the probe (step 2) are the only remote route; until they
  exist `ssh` asks.
