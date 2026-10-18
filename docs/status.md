# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address (test
alarm 18 October).

## Done

- Step 0 (all but the third machine). 1.1 fences. 1.2 the reference copy.
  1.3 the baseline (node1 not measured). 1.6 the watcher. 1.7 reference,
  profiles. 1.8 `support/db`, the off-site dump. 1.9 eleven contracts. 1.10
  fetch gate, landing, the carried reader, the model client, legal.
- Step 1b, closed: the question and fix weights and their launchers, `bin/q`,
  the sample and the two tiers, the reading-limit check, the timer hook,
  `qv4-full-tier` 04:30. Proof: a question session in 69 s. The gate's
  staging step now runs in its worktree.
- 1.11 the thin slice: `registers/party_returns` (the first lane),
  `pub.party_return_totals`, and the plain page
  `python -m products.published_site`. The real load landed 152 returns from
  the old folder by hash; 32 read to a row, 120 set aside with a reason (115
  no text layer, 5 carded). Against the frozen site: 23 party-years equal,
  1 differs (Labour 2020, original against amendment, carded).
- 1.6 widened: the watcher's `carve-out` item asks systemd for every
  carve-out unit (red when one the release needs is down, or one seen running
  here stops) and reads the stop list, so `v3-audit`'s silence is not red.

## Next

A founding session on 19 October: compare that morning's release with
`2026-10-18T1334` (`checks/release_compare.py`); if green and within the
yardstick, stop batch 3 (`v3-audit`, on the stop list). 1.5 waits on Arthur
(the queue). When node1 returns, re-measure it and stop its halves.
Then step 1 closes.

## Half-done

- 1.4: batch 1 (press graph, meaning index, `nzme-archive-backfill`) stopped
  01:1x 18 October; the 06:17 release green after it. Batch 2 stopped
  and disabled 11:35 18 October, node2: 18 units (derive chain and feeds,
  old apps and helpers, reference downloads, `querynz-llm@1`,
  `querynz-embed`); the gateway routes the chat model to `:8020`. A
  release by hand at 12:36 went RED: its search gate reads `:8300`, so
  `querynz-pi-web` is back on and in the carve-out (carded; the release
  addresses nothing else in batch 2). The 13:34 release: green, inside the
  yardstick against `2026-10-18T0617`. Owed: the 19 October
  release green against `2026-10-18T1334`; then batch 3. Node1's half waits
  for node1; the positive half for the next declaration listed.
- 1.5: first commit by Arthur's hand (7f9f0bb5, 18 October), unpushed while
  node1 is down; the second commit and the tag need his hand (the board's
  open blocker).

## Known gaps left on purpose

- Until step 2: `ssh` asks, node1 gets no job files; the party returns lane
  has no `qv4-` job, donor rows or page reader.
