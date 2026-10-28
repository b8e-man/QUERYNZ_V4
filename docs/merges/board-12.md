# board-12: rulings 111 and 112, entities only in the results pane, the graph tab gone, the collapse section
branch: session/board-12 (pushed; two commits on 50b1350)
session: board-12 (Opus, build, scope products/board/)
raised: 2026-10-28
claims: products/board/ (collapse.py new, panes.py, server.py, graph.py, search.py, dossier.py, people.py, check.py,
assets.py, static/graph.js, static/README.md, spec.md; tests/test_collapse.py new, test_results.py, test_real.py,
test_fields.py, test_near.py, test_removed.py, test_panes.py, test_graph.py);
lessons/when-rows-move-to-a-new-surface-move-the-checks-that-read-them-there.md; docs/status/board.md.

## What it does

1. **Ruling 111 (1): entities only.** The results pane lists entities in every state of the switch:
   - first the groups the matching rows fall in (as ruling 108's entity state listed them, no "matching here");
   - then each row in no group as a single-row entity: its title, register and view, "1 row, 1 register", the
     fields it matched under "any field may match". Its name opens its dossier.
   No row's card (fields, citation) is in the pane; a row is read in its entity's dossier (ruling 110). The near
   matches below are listed as entities too. Each tab by matched field (108) holds the entities one of whose rows
   matched it; the tab's count is those entities, with "+" where rows matched past the 50 per view read. Those rows
   are said and never counted. The rows matched per register are counted above the entities, never listed.
2. **Ruling 111 (1): the switch.** "show: rows · entities" sits on the graph's pane alone and governs the graph
   alone. `g=entities` stays in the address; graph.js keeps the dossier chosen (`d=`) in the switch's links.
3. **Ruling 111 (2): the graph tab gone.** The bar holds search and use cases. `/graph?…` and `/?tab=graph…` answer
   303 to the search page on the same query, boxes and state with `gv=1`: the graph drawn beside the results by the
   server (its data inline, the SVG inside `<noscript>`), centred on `c` or `d` with its dossier under it, else the
   whole search (`server.graph_redirect`). Live `board.paths` and `board.pins` hold no rows, and both always linked
   to `/?q=&p=`, never to `/graph`. A live test plants a saved path in the scratch schema, opens it from `/saved`,
   and follows an old `/graph?…&c=` bookmark through the 303 to the drawn graph.
4. **Ruling 112: the collapse section (`collapse.py`).** A closed "collapse" section above the entities opens to a
   fixed list: the links lane's groups (ticked, fixed), a shared first and last name (`pub.names.fl_key`), a shared
   full name with middle names (`full_key` where `has_middle`), a shared registered address (a company's
   registered office from `pub.company_addresses`, read by an organisation row's own key, never a person's row), a
   shared official number (an organisation row's own NZBN, company, charity or incorporation number; a holder's,
   body's or tender's number never folds). `cl=` per criterion rides every href, so a view reopens folded.
   - Entities sharing a key, through any chain, become one entry: "collapsed here by shared name; not a link".
   - Its dossier (`d=fold:<criteria>:<members>`) lists the members as the entities they are, each opening its own.
   - The graph beside the results folds the same way; the node carries the same words (double border).
   - A suppressed row carries no key. The section only reads; nothing is written.
5. Also: the dossier printed a director's company as its bare key (`company: companies/…`) since board-11; it now
   names it, linked (ruling 92 (2)). Found by moving check item 16 to where rows now live (the lesson). graph.js's
   side-pane failure message called `say()` out of its scope; fixed.

## Cost (live, 28 October)

| Page | Before (board-11 notes) | Now, no fold | Now, every criterion |
| --- | --- | --- | --- |
| hart | 2.18 s, 1.5 MB | 1.86 s, 463 KB | 2.03 s, 575 KB |
| Graeme Hart (entities) | 3.03 s | 2.97 s | 2.96 s |
| John Smith | | 3.19 s, 364 KB | 3.19 s, 433 KB (472 entries fold to 431) |

The results no longer read row citations or far rows for the pane. Folding costs at most 0.15 s: one query on
`pub.names` by ref, one on `pub.groups` by group, one per suppressing view, and the registered offices
(a 36 ms scan) only when that box is ticked. The search floor holds (`test_a_search_answers_within_two_seconds`
and the tabbed search in both states, green).

## Verified

- `python -m products.board check`: green (80 s). New items:
  - **26**: entities only, no row's card in the results pane outside a dossier, under tabs, any field and all
    fields, in both states; the switch once on the graph's pane; no graph tab; the old address lands drawn.
    `test_real` plants a row card (lone rows rendered as rows) and item 26 goes red.
  - **27**: every criterion ticked for "John Smith" in both states. It checks:
    - fewer entries than unfolded;
    - every folded entry and node says "collapsed here by …; not a link" and nothing that reads as confirmed;
    - a fold's members are each a group pub.groups holds, and its dossier lists them;
    - pub.groups and pub.links are counted and hashed the same before and after.
  Items 6, 9, 16, 19, 21, 23 and 25 were moved to entities. Item 23's tab counts are now checked against entities
  read apart from people.gather.
- `tests/test_collapse.py` (15): a test per criterion on fixture rows, and every statement checked to be a select
  touching neither pub.links nor pub.groups. Mutations turn it red: dropping `has_middle`, letting a tender id or
  a person's number fold, and asking a person's row for an address.
- `tests/test_real.py`, `test_night`, `test_canvas`, `test_dossier`, `test_collapse`, `test_results`: green together.
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 43.6 s.
- Headless Chrome on a scratch server (127.0.0.1:8495):
  - "graeme hart" in rows: 46 entries, all entities, 0 row cards, the switch in the graph's pane only, bar
    "search · use cases".
  - A real click on an entity result opened the graph and the dossier, with `d=` in the address and the switch's link.
  - Clicking the switch reopened in entities with the same dossier and the graph.
  - `/graph?q=graeme+hart&all=1&g=entities` landed on `/?…&gv=1` with the graph drawn inline (15 nodes, 6 entities).
  - "john smith": clicking the collapse summary opened it; ticking "name" and applying gave `cl=name` and 18 folded
    entries (472 → 432), each saying "collapsed here by shared name; not a link".
  - A real click on a fold opened its dossier, listing 52 members.
  - With `gv=1` a fold node was drawn with the same words.
  - At 1000 px the graph stacks under the results.
  - 43 requests, none off the board. The only console line is the browser's `/favicon.ico` 404, as before.

## Known limits

- `panes.hit`, a row's card, is now used by no surface. Its tests (beehive, diaries, hansard, far) still hold its
  rendering. A later fix may retire it or give it to the dossier.
- A folded entry's keys are read once per page. An entity under two tabs keeps the number keys of the rows its
  first tab held.

## The integrator must

1. Merge `session/board-12`.
2. **Restart `qv4-board` at the release.** This brings a new `graph.js` hash, the `/graph` redirect, the collapse
   section and a new page layout. No table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` for the one new lesson.

## Result (integrator, 28 October 19:20 NZDT)
Merged 3fcdd27, gate green at the first run: the first gate in its ruling-113 shape, 17 minutes (18:59 to 19:16) against 25 to 27 for the full run. Released; `qv4-board` restarted 19:20. The unused row card (`panes.hit`) is noted for a later board fix. Branch and the working copy retired.
