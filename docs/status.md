# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-24 NZDT. **Process:** ruling 131 (31 Oct) ended the
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

## Running

- The bulk ingest from the MCP every six hours; each pull queues the
  reader lanes' loads and the news load.
- The old estate's tables copied in nightly (23:50 to 05:45).

## Half-done

- Provider asks open: estate-news-gaps@2026-11-21 (77 old-only sites,
  stale sites, date holes, undated coverage); the party-site back-fill.
- Held back until after the council landings due 24 Nov: disclosure
  statements, Electoral Commission, council minutes, ERA and courts.
- 4.5: the rebuilt site's build is refused since 23 Nov: the
  Commission's over-$20,000 list was re-captured on 18 Nov with a new
  hash the frozen listing lacks, so its 305 rows are left out and the
  commission gate is red. Waits on Arthur.
- The full tier: board, report and template tests over the real data
  (timings, statement timeouts, changed dossiers) and three takeover
  script tests fail; not yet looked at.

## Waits on Arthur

- The rebuilt site's pin (above). The Insolvency Register API
  subscription and the PPSR account (8.4); letters (Dunedin, TPK,
  Police); rulings 69, 75; the 15 unsplittable courts documents.
