# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-26 NZDT. **Process:** ruling 131 (31 Oct) ended the
plan's gate process; work runs on Arthur's word. **Boxes:** two, both
take every job (ruling 145); jobs run from the release copy
(`python -m support.installer release` on each box after every push).

## Done

- To 14 November: steps 0 to 3, 4.1 to 4.4, 4.9, 5.1 to 5.5, 6.1 to
  6.3, step 8; rulings 132 to 175; the takeover drill passed.
- News register (17 to 24 Nov): the old estate's copy and the
  provider's estate-news in one table; 180 sites judged, 38 retired,
  9 ready; a site the provider holds elsewhere is ready only when every
  old address is there (20 Nov).
- Comments (18 to 24 Nov): the provider's pages, estate-comments
  (Coral, WordPress) and estate-substack read into news_private.comments,
  each linked to its article and commenter; Substack free posts into
  the articles table once their files land.
- The gold sample: tranche 7 (140 questions) on the board.
- 25 Nov: the off-site restore rehearsal passed, equal, in 6.1 h (was
  over 12 h: it ran on node1 over NFS; now pinned to node2). Links:
  middle names that differ are two people (pub.links_different,
  996,528 pairs); every near link says why. Lane reds of 24 Nov fixed.
- 26 Nov: models by schedule: the 27B by day on both boxes, Flash-Next
  on node2 22:00-05:45 (shift_tick). The news read (news-article v1,
  gates 2) runs row after row (until_empty). Every reading carries its
  serving id (support/recipes). Review agent removed (ruling 180).

## Running

- The bulk ingest from the MCP every six hours; each pull queues the
  reader lanes' loads and the news load.
- The old estate's tables copied in nightly (23:50 to 05:45).
- The news read: 2.75 million unread, about 50 days.

## Half-done

- Provider asks open: estate-news-gaps@2026-11-21 (first landings
  26 Nov); estate-lane-gaps@2026-11-25 (REA 27, WorkSafe 5, tenancy 504).
- Reader configurations (support/recipes): tranches 2-6 to build:
  recipes, golden sets, trials, the selector, the other lanes.
- Held back until after the council landings due 24 Nov: disclosure
  statements, Electoral Commission, council minutes, ERA and courts.
- 4.5: the rebuilt site's build is refused since 23 Nov: the
  Commission's over-$20,000 list was re-captured on 18 Nov with a new
  hash the frozen listing lacks, so its 305 rows are left out and the
  commission gate is red. Waits on Arthur.
- Insolvency capture held after four nights of transport errors (card).
- Board chat shelved (Arthur, 26 Nov); it would have to follow the
  box's standing model.

## Waits on Arthur

- The rebuilt site's pin (above). The Insolvency Register API
  subscription and the PPSR account (8.4); letters (Dunedin, TPK,
  Police); rulings 69, 75; the 15 unsplittable courts documents.
