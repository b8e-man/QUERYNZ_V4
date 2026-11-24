# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-25 NZDT. **Process:** ruling 131 (31 Oct) ended the
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

## Running

- The bulk ingest from the MCP every six hours; each pull queues the
  reader lanes' loads and the news load.
- The old estate's tables copied in nightly (23:50 to 05:45).

## Half-done

- Provider asks open: estate-news-gaps@2026-11-21 (first landings
  26 Nov); estate-lane-gaps@2026-11-25 (REA 27, WorkSafe 5, tenancy 504).
- Links: shared-associate@1 built, first in the 26 Nov 07:45 build;
  document co-mention being measured for the same build.
- Held back until after the council landings due 24 Nov: disclosure
  statements, Electoral Commission, council minutes, ERA and courts.
- 4.5: the rebuilt site's build is refused since 23 Nov: the
  Commission's over-$20,000 list was re-captured on 18 Nov with a new
  hash the frozen listing lacks, so its 305 rows are left out and the
  commission gate is red. Waits on Arthur.
- The full tier: 3 speed tests over the Beehive group miss by 2-15%
  on a loaded box (was 26 failures); a quiet re-run owed.
- Insolvency capture held after four nights of transport errors (card).

## Waits on Arthur

- The rebuilt site's pin (above). The Insolvency Register API
  subscription and the PPSR account (8.4); letters (Dunedin, TPK,
  Police); rulings 69, 75; the 15 unsplittable courts documents.
