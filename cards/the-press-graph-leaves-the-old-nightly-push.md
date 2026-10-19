# The press graph leaves the old nightly push, on Arthur's word after the election
kind: finding
state: open
use-case: the off-site copy (track B)
session: offsite
opened: 2026-10-19

The press graph (`extractions`, 276 GB on disk) has had no writer since 18
October (step 1.4 stopped `feed-parties` and `gazette-feed`). Track B's copy
treats it as frozen: one full copy on 19 October (stamp 20261019T074541,
5.4 GB sealed), sent again only when its write counters move or every 28
days, inside the bucket's 45-day rule. Restored from the bucket the same
day: 75 of 75 tables equal, 470 million rows. Each
nightly record lists any press-graph table that moved (`frozen_moved`), so
a writer coming back is seen the night it writes.

The old nightly push still sends it whole every night: about 10.7 GB and 48
minutes of the satellite link. Taking it out is a change to the old
estate's job (hard limit 22), so it is Arthur's word, not before the
election. The queued decision `whether-the-press-graph-leaves-the-old-nightly-push`
holds the default (not yet).

When: after 7 November, the new copy restored to equality from the bucket on
19 October (`docs/merges/offsite-2b`); Arthur says so, and the old push's
`DBS` loses `extractions`. The database itself is never dropped without his
word.
