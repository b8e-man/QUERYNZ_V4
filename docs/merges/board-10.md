# board-10: ruling 106 (2), the lineage frame for the links lane's related grade
branch: session/board-10 (pushed, 2dfa72c; one commit on ada4b94)
session: board-10 (Opus, build, scope products/board/)
raised: 2026-10-28
claims: products/board/ (lineage.py new, graph.py, people.py, links_view.py, panes.py, server.py, check.py, catalogue.py,
static/graph.js, spec.md; tests/test_lineage.py new, test_real.py, test_results.py);
lessons/pick-the-node-that-stands-for-several-rows-by-an-order-every-answer-shares.md; docs/status/board.md.

## What it does

1. **Server side (`lineage.py`).** `pub.links`' grade `related` is read by row key for every row in hand at once,
   then once more per round for a chain's new ends (at most 3 rounds). Each chain is one frame: the companies in the
   evidence's date order (`earlier` before `later`, then registration date, then key), labelled with the relation and
   the years ("succeeded by · 1987 → 2011, 2013"; arrows only where it is a true chain). Each company is its own node:
   a row, a lone row, or its own entity, never one. Each shared person is drawn once, as their row on the earliest
   company (rows state) or their group (entities), joined to every company by the record relation their own row
   asserts ("director of"), cited by that row. A person whose row is suppressed or not found is counted, never named.
   No name is taken from the evidence. The relation is read from `pub.links.relation`, else from the evidence's
   own copy (see below).
2. **Canvas (`graph.js`).** The frame is a compound node in a new key colour, `lineage` lime `#80f040` (19 or more
   apart from every edge colour in OKLab; 12:1 on the picture; a fill at 10% under which ink still reads at 4.5:1 or
   more). It has a double border and its label on top. The companies sit left to right and the people beneath them,
   five to a row. The lineage line is solid, arched, with an arrow from earlier to later. Near keeps its colour and
   dash alone. Tapping the frame does nothing. A grown hop that brings a frame moves nodes already drawn into it. A
   fold lets the frame's members go rather than removing them with it. "Spread" keeps the frame.
3. **Panes.** A row's links pane and the entity pane list related links under "Related companies". Each shows the
   relation read in date order, the other company and the years, and the people on both (their rows on this side).
   Suppressed people are counted. In the results pane, an entity, or a company row, that has a related link says
   "related". The word is needed for rows: the live succession companies sit in no group.
4. Also: the board now has words for ruling 107's rule `organisation-one-live-company@1`. Without them
   `test_real` was red.

## Cost (live, 28 October, load average about 2)

- The lineage step adds 13 to 16 ms per graph ("hart", "smith", "Graeme Hart", "anderson lloyd", both states).
- Graph builds: hart 1.95 s / 1.79 s, smith 1.96 s / 2.00 s, Graeme Hart 1.85 s / 1.76 s.
- Centred on a succession company: 0.10 s / 0.11 s.
- The results word costs one query by key over the organisation rows listed.

## Verified

- `python -m products.board check`: green in 64 s. New item 24 is centred on ANDERSON LLOYD TRUSTEE COMPANY
  LIMITED, 1987, which has two successors (2011, 2013). It checks both states:
  - date order against pub.companies' own dates;
  - three distinct company nodes, no two in one group;
  - every lineage line a related pair;
  - ten people, each once, each joined to two companies;
  - the frame placed before its children;
  - the line neither dashed nor in near's colour;
  - both panes say "Related companies".
  A planted merge (the frame's companies relabelled to one node) turns it red on the live tables: that is
  `test_real::test_the_lineage_check_goes_red_when_a_frame_merges_its_companies`.
- `tests/test_real.py`, `test_night`, `test_canvas`, `test_lineage`: green together, 1 m 27 s.
- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 42.9 s (the sample fill 41.4 s).
- Fixture tests (`test_lineage.py`, 16) were mutation-checked. Each of these breaks at least one test:
  reversing the evidence's order, dropping the merge of a person's second row, and ignoring suppression.
- Headless Chrome on a scratch server (127.0.0.1:8491):
  - Rows and entities: one frame, double lime border, three companies on one row in the answer's date order,
    distinct nodes (rows; lone rows in entities), ten people beneath, each joined to two or more companies.
  - Two lineage lines, solid; near lines still dashed.
  - Growing the latest company, then folding it, keeps 13 members. This was 23 before the fix in the lesson.
  - "Spread" keeps the frame.
  - The search for "anderson lloyd trustee" shows "related" on three rows. A click opens the graph beside the
    results with the frame.
  - No console error, no request off the board.

## Known limits

- Without script, the SVG draws the lineage line but no frame. The note under the picture says so.
- **Live `pub.links` has no `relation` column** after the 14:09 `qv4-links-build`, although `links.links` has one.
  `publish.sql`'s append did not reach the view. The board reads the evidence's copy meanwhile. A links fix should
  republish; nothing on the board changes when it does.
- `products/report/walk.py` still treats `related` as near. That file is outside this scope; it needs a fix session
  on products/report.

## The integrator must

1. Merge `session/board-10`.
2. **Restart `qv4-board` at the release.** This brings a new `graph.js` hash, a new edge kind in the key, and new
   panes. No table, unit or setting changes.
3. Regenerate `lessons/INDEX.md` for the one new lesson.
4. Look at `pub.links.relation` (above): republish the links view.

## Result (integrator, 28 October 14:48 NZDT)
Merged c492917, gate green at the second attempt to start it (the first stopped before the gate: the new lesson's rule line was 248 characters; shortened). Released; `qv4-board` restarted 14:48. `pub.links.relation` was republished live by the integrator at 14:30 with the lane's own publish DDL (the gate's staging skips a lane with no load.py: lesson filed), so the board reads the relation from the column. The report's walk is fix-products-report-3, launched by the integrator. Branch and the working copy retired.
