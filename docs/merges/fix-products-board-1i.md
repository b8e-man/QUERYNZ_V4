# fix-products-board-1i: the board catalogues the three Beehive views and Hansard's daily PDF (carries hansard-2)
branch: fix/products-board-1 (pushed, f43b5d1; carries hansard-2, merged in from integrate/hansard-2 and not yet on main)
session: fix-products-board-1 (Opus, fix, scope products/board/)
raised: 2026-10-27 (written to the session's scratch folder: the fence refused the inbox link, card
`a-fix-session-cannot-write-its-merge-request-into-the-inbox`)
claims: products/board/ (catalogue.py, panes.py, spec.md; tests: new test_beehive.py, test_catalogue.py's published list,
test_hansard.py's view list); lessons/take-a-name-order-from-a-real-record-when-the-live-view-holds-none.md;
docs/status/board.md. No card opened or closed.

## Before the gate: publish hansard-2 on live first

`bin/merge-gate` runs the tests before staging publishes. This branch catalogues `pub.hansard_days`, which is on
live only once hansard-2's `publish.sql` runs, so gated as things stand `tests/test_real.py` fails on exactly one
line: `hansard_days: in the catalogue but not published (pub.hansard_days missing)`. Publish hansard-2's views on
live (its load, `python -m registers.hansard.load`) and then gate this branch. The live check is otherwise green:
the three Beehive views were the red, and they are catalogued.

## What it does

1. **The register.** "Beehive: releases, speeches and features" in `REGISTERS` straight after Hansard; in the House's
   family (no colour added, the contrast tests green); `MAIN_VIEW["beehive"] = "beehive_releases"`. 30 registers in
   14 families.
2. **The release** (`beehive_releases`): titled "<title> · <type>"; type, kind, words, the ministers and portfolios
   the site tags, the provider's topic and quote counts labelled as its model's, versions, origin, the provider's
   reading (`mcp_state`), captured, source note; the record's own day; the page's address as the citation. New
   `catalogue.Say` (a line a row carries where a column holds a value, data, shown in the pane and the hit):
   "read from the newest of N versions" (versions > 1), "the title, day and words are the old estate's: its scraper's
   reading, original not held" (origin "old estate"), "captured by the provider on <day>, not yet read" (mcp_state
   "captured only"). Every row: the estate did not fetch the page (ruling 78). Its ministers in order and its
   annotations joined beneath.
3. **The minister tag** (`beehive_release_ministers`): one row per tag, titled `<name> · tagged on "<title>" · <day>`,
   the site's slug, its order, the release as parent pointer. Kind `event`: no person pane. Name **given-family**: the
   MCP's own records tag "Hon Chris Bishop", "Hon Shane Jones" (three records read through `records`; live held 0
   minister rows, and the lane's fixture "Minister A" fixes no order). The honorific comes off the front (ruling 85).
4. **The annotation** (`beehive_release_annotations`): titled "The source's annotation (made by its model, not ours)
   · <topic|quote>: <value>", the same heading on the release's join and in its note, the provider's model named
   (`made_by`). Searched by value only. No Relation, no Name, no `names`, no person; its only pointer is the release.
5. **The daily PDF** (`hansard_days`, hansard-2): titled "<day> · daily PDF"; the provider's title, pages, words,
   captured, the provider's hash, versions, whether the old transcript holds the day and how many of its subjects the
   PDF's text carries; the PDF's address as the citation; a `Join` to the sitting by day, and the sitting gains a
   `Join` back ("The daily PDF (the MCP)").

## No edge to the House

`pub.members` publishes key, election, name, name_key, party, electorate, candidate and dates: no Parliament member
id and no slug. A minister tag carries a name and the site's slug, so the only join left is by name, a link made by
looking. No Relation, no pointer. As with Hansard's turns, the shared id is a lane's to publish.

## Checks

- `python -m products.board check` against live: one problem, `pub.hansard_days missing` (above). The Beehive
  views: every shown and searched column present.
- `pytest -m slow products/board/tests/test_real.py`: 15 passed, 1 failed, the same line.
- `hansard_days` against the real data, off live: hansard-2's load into the sample's scratch schema
  `scratch_fix_products_board_1_hansard`, with the two Hansard corpora's 2,245 arrival rows (hash, seq, record id,
  landed_at) copied from live `mcpsource.arrivals` into `scratch_fix_products_board_1_mcp`. 1,862 days, 137 also held
  as the old transcript's sections. Its `publish.sql` was applied in that schema: every column the catalogue reads is
  present in both days and sittings, and a day's pane is titled "20 November 2024 · daily PDF", cites the PDF and
  links the sitting. Both scratch schemas are regenerable and may be dropped.
- `products/board/tests`: green (test_beehive: a fixture case per view; the contrast tests green).
  `QV4_INTEGRATOR=1 bin/fast products/board`: green in 46.4 s.
- A live release pane rendered in 0.01 s, with the old-estate line, the ministers join, the annotation heading and
  the did-not-fetch line. A search for "Waioweka" lists the Beehive register in 1.4 s.

## For the integrator to note

- Live `pub.beehive_releases` holds 55,358 rows, all origin "old estate"; `mcpsource.arrivals` holds 62,527 beehive
  records that no load has read into it (0 minister and 0 annotation rows). That is the beehive lane's job
  (`qv4-beehive-load`, proposed in its spec), not the board's. File it as a card if the job is not yet queued.
- A release's `published_at` is not shown: the pane gives the record's own day, and the board's date format would
  re-zone a served timestamp. A known limit in docs/status/board.md.

## At the merge

The integrator restarts `qv4-board` at the release, after hansard-2's views are published. No table, unit or job
changes. One lesson filed (above).

## Result (integrator, 27 October 10:20 NZDT)
Merged 3063cc7, gate green at the third run (see hansard-2.md's result for the two refusals: the catalogued-before-published day view, then a transient shape change at the provider). Released; `qv4-board` restarted; the board's live check is green with the Beehive's three views and Hansard's daily PDF catalogued. Branches and the working copy retired.
