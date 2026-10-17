# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, proven
by the watcher's test alarm at 01:08 on 18 October.

## Done

- Step 0 (all but the third machine). 1.1 fences. 1.2 the reference copy.
  1.3 `docs/baseline.md` (node1 not measured). 1.6 the watcher. 1.7 reference,
  profiles. 1.8 `support/db`, `qv4-offsite-dump`. 1.9 eleven contracts. 1.10
  fetch gate, landing, the carried reader, the model client, `docs/legal/`.
- Step 1b, closed: the question and fix weights and their launchers, `bin/q`,
  the sample and the two tiers, the reading-limit check, the timer hook,
  `qv4-full-tier` 04:30. Proof: a question session in 69 s; the slice's
  tests in the fast tier. The gate's staging step now runs in its worktree.
- 1.11 the thin slice: `registers/party_returns` (the first lane, with the
  first `sample.list` and `load.py`), `pub.party_return_totals`, and the
  plain page `python -m products.published_site`. The real load landed 152
  returns (671 MB) from the old folder by hash; 32 read to a row, 120 set
  aside with a reason (115 have no text layer and wait for the page
  reader; 5 at the declaration page, carded). Against the frozen site: 23
  party-years equal, 1 differs (Labour 2020, original against amendment,
  carded). The fast tier: 14 s for the whole repository, 6 s for the lane.

## Next

A founding session: 1.4 batches 2 to 4 (each after a green scheduled
release; 18 October's was green). 1.5 waits on Arthur (the queue). When
node1 returns, re-measure it into `docs/baseline.md`. Then step 1 closes
and the integrator starts.

## Half-done

- 1.4: batch 1 stopped and disabled 01:1x on 18 October (`nzme-archive-backfill`,
  `v3-extract`, `querynz-crawler`, `querynz-mint-lane`, `querynz-research`,
  `querynz-sweep`, `querynz-embed-backfill`, `querynz-embed-index-ship`).
  The `newsscrapers` timers are back since 09:06 on 18 October; the first run
  skipped NZME by ruling. Normal daily change measured (`docs/baseline.md`,
  last section; `checks/release_compare.py`). Batch 2 after a green scheduled
  release: the derive chain, the old apps, `querynz-llm@1`, `querynz-embed`;
  then `v3-audit` last.
- 1.5: first commit made by Arthur's hand, 7f9f0bb5 in the live folder,
  02:5x on 18 October. Not pushed: the old repository's only remote is the
  mirror on node1, which is down. The second commit and the tag still need
  his hand (the one open blocker on `docs/board.md`).

## Known gaps left on purpose

- Until step 2 exists, `ssh` asks and node1 gets no job files. The party
  returns lane has no `qv4-` job yet (the gate loads it at each merge), no
  donor rows and no page reader.
