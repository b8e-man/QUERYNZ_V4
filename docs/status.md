# Where the build stands

Overwritten at every close; under 3 KB. What happened is in the cards, the
lessons and the commit messages.

**Date:** 2026-10-18. **Step:** 1. **Boxes:** node2 is the primary since the
17 October failover; node1 is down and rejoins as the standby after a
rewind (Arthur's). **Alarm channel:** the old estate's ntfy address, proven
by the watcher's test alarm on 18 October.

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
  have no text layer and wait for the page reader; 5 at the declaration
  page, carded). Against the frozen site: 23 party-years equal, 1 differs
  (Labour 2020, original against amendment, carded). The fast tier: 14 s.

## Next

A founding session on 19 October: compare that morning's release with
`2026-10-18T1334` (`checks/release_compare.py`); if green and within the
yardstick, stop batch 3 (`v3-audit`). 1.5 waits on Arthur (the queue). When
node1 returns, re-measure it and stop its halves. Then step 1 closes.

## Half-done

- 1.4: batch 1 (press graph, meaning index, `nzme-archive-backfill`) stopped
  01:1x on 18 October; the 06:17 release ran green after it. Batch 2 stopped
  and disabled 11:35 on 18 October on node2: 18 units (derive chain and
  feeds, old apps and helpers, reference downloads, `querynz-llm@1`,
  `querynz-embed`); the gateway routes the chat model to `:8020` alone. A
  release by hand at 12:36 went RED: its search gate reads `:8300`, so
  `querynz-pi-web` is back on and in the carve-out (carded; nothing else in
  batch 2 is addressed by the release). The 13:34 release ran green and is
  inside the yardstick against `2026-10-18T0617`. Owed: the 19 October
  release green against `2026-10-18T1334`; then batch 3. Node1's half waits
  for node1; the positive half for the next declaration listed.
- 1.5: first commit made by Arthur's hand, 7f9f0bb5 in the live folder, on
  18 October; not pushed while node1 (the only remote) is down. The second
  commit and the tag still need his hand (the open blocker on the board).

## Known gaps left on purpose

- Until step 2 exists, `ssh` asks and node1 gets no job files. The party
  returns lane has no `qv4-` job yet, no donor rows and no page reader.
