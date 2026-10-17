# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages. Written by the founding session during
step 1; by the integrator after.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, proven
by the watcher's test alarm at 01:08 on 18 October.

## Done

- Step 0 (all but the third machine). 1.1 fences. 1.2 the reference copy at
  `/home/user/qnz3-ref` (old tests only with no DSN set). 1.3 `docs/baseline.md`
  (node1 not measured; twelve differences). 1.6 the watcher (`qv4-checks-board`
  07:30, `qv4-checks-heartbeat` 09:00/21:00). 1.7 `reference/`, `support/profiles`
  (corrections kept outside git). 1.8 `support/db`, `qv4-offsite-dump` 03:05.
  1.9 eleven contracts in `docs/contracts/`. 1.10 fetch gate, landing
  (`/mnt/hdd2/qv4-docs`), the carried reader, the model client, `docs/legal/`.
- Step 1b, built: question and fix weights in the hooks; `bin/ask`, `bin/fix`,
  `bin/q`, `bin/fill-sample`, `bin/fast`, `bin/full-tier`, `bin/lessons`
  (recall 3/8 at eight); the inbox; the reading-limit check; the timer hook
  and `checks/session_times`; the gate's staging step; `qv4-full-tier` 04:30
  (first run 626 passed in 28 s). `bin/fast`: 8.6 s for the whole repository.

## Next

1b's proof is in (one question session, 69 s, clean). Next a founding
session: 1.11, then 1.4 batches 2 to 4 (each after a green scheduled
release; 18 October's was green). 1.5 waits on Arthur (the queue). When node1 returns,
re-measure it into `docs/baseline.md`.

## Half-done

- 1.4: batch 1 stopped and disabled 01:1x on 18 October (`nzme-archive-backfill`,
  `v3-extract`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`,
  `querynz-sweep`, `querynz-embed-backfill`, `querynz-embed-index-ship`).
  The `newsscrapers` and `newsscrapers-daily` timers are back since 09:06
  on 18 October; the first run skipped NZME by ruling. Normal daily change measured (`docs/baseline.md`, last section;
  `checks/release_compare.py`). Batch 2 after a green scheduled release:
  the derive chain, the old apps, `querynz-llm@1`, `querynz-embed`; then
  `v3-audit` last.
- 1.5: first commit made by Arthur's hand, 7f9f0bb5 in the live folder,
  02:5x on 18 October. Not pushed: the old repository's only remote is the
  mirror on node1, which is down, so the old pre-push gate has not run on it
  yet. The second commit and the tag still need his hand (the one open
  blocker on `docs/board.md`). Three baseline findings are carded too.

## Known gaps left on purpose

- Until step 2's installer and probe exist, `ssh` asks and node1 gets no
  job files. No module has a `sample.list` or a `load.py` yet: 1.11 writes
  the first.
