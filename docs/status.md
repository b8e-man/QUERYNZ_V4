# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages. Written by the founding session during
step 1; by the integrator after.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, present
and proven (the watcher's test alarm, 01:08 on 18 October).

## Done

- Step 0 (all but the third machine). 1.1 the fences. 1.2 the reference
  copy at `/home/user/qnz3-ref` (run old tests there with no DSN set).
  1.3 `docs/baseline.md` (node1 not measured; twelve differences).
- 1.6 the watcher: `qv4-checks-board` 07:30 and `qv4-checks-heartbeat`
  09:00/21:00 on node2; `checks/`, `support/alarm`, `support/jobrun`.
- 1.7 `reference/` and `support/profiles`; the corrections stay outside git
  at `/home/user/querynzv4-work/live/reference/corrections.jsonl`.
- 1.8 `support/db` (42 schemas, grants, `bin/db-setup`) applied to both
  databases; `qv4-offsite-dump` 03:05 nightly, first run sent.
- 1.9 eleven contracts: `docs/contracts/`, each with a test (`keys/`,
  `support/*`, `links/`, `products/templates`).
- 1.10 `support/fetchgate`, `support/docstore/landing` (store on
  `/mnt/hdd2/qv4-docs`), `support/docread` (carried, 203 tests, `read.py`
  is the contract's door), `support/modelclient`; `docs/legal/`.
- Fast tier: 599 tests, 19 s.

## Next

Step 1b, then 1.11. 1.4 batch 2 after the 06:15 release on 18 October runs
green, then batches 3 and 4. 1.5 waits on Arthur (the queue). When node1
returns, re-measure it into `docs/baseline.md`.

## Half-done

- 1.4: batch 1 stopped and disabled 01:1x on 18 October (`nzme-archive-backfill`,
  `v3-extract`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`,
  `querynz-sweep`, `querynz-embed-backfill`, `querynz-embed-index-ship`;
  four old failure alarms for the killed runs, expected). Held until the
  NZME commit lands: `newsscrapers`, `newsscrapers-daily` timers. Normal
  daily change is measured (`docs/baseline.md`, last section;
  `checks/release_compare.py`). Batch 2 after a green scheduled release: the
  derive chain, the old apps, `querynz-llm@1`, `querynz-embed`; `v3-audit` last.
- 1.5: BLOCKED. The session's permission mode refuses every write into the
  live old folder. The rehearsed NZME change is the patch at
  `/home/user/querynzv4-work/live/nzme-freeze-commit.patch`; the decision
  queue has the commands.

## Known gaps left on purpose

- The hooks know `founding`, `integrator`, `build`; `fix` and `question`
  come in 1b.1. The merge gate is one tier until 1b.7. Until step 2's
  installer and probe exist, `ssh` asks and node1 gets no job files.
