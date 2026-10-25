# fix-products-board-1c: graph edges listed, not overlapped; rule ids in words (ruling 84)
branch: fix/products-board-1 (pushed, 5c8f184; one commit on bf9cf6e)
session: fix-products-board-1 (Opus, fix, scope products/board/; third use of the name)
raised: 2026-10-25 (written to the session's scratch folder: the fence refused the inbox link)
claims: products/board/ (catalogue.py, graph.py, panes.py, check.py, spec.md; tests test_graph.py, test_catalogue.py,
test_near.py, test_panes.py, test_real.py); lessons/a-no-overlap-check-on-a-small-picture-passes-a-broken-placement.md;
docs/status/board.md. No card opened or closed.

## What it does

1. **Rule ids in words.** `catalogue.RULE_WORDS` gives each links rule plain words, written from the links lane's own
   descriptions (`links/rules.py`, `links/build.py`): all 14 ids `pub.links` carries, the 12 the brief named plus
   `own-return` and `coupled-name`. `name-only@1` reads "same name, nothing else". An id the table lacks reads
   "links rule <id>". The id and version appear as "(links rule name-only, version 1)" only in an edge's tooltip and in
   the list, never as a label. The row pane's links section reads the same words (it printed "rule name-only@1").
2. **One line per pair.** `graph.lines`: two rows joined more than once get one line. Its stroke is the kind of the
   first cause in the key's order, and its tooltip lists every cause. The key still counts every cause.
3. **No label over another.** Each line has a number, an href to the row that asserts its first cause. `graph.place`
   (pure, deterministic) puts the number at the midpoint and moves it along the line until it clears every label,
   number and circle. If nothing clears, the number is left off the picture and the list says so. Node labels sit
   below, else above, right or left of the circle, shortened step by step. The register line goes last, and a label
   with no room keeps its text in the tooltip. The two-ring fan stays. Under the key: "Edges, by number", an ordered
   list giving the two row titles, then each cause with its kind, its words, the rule reference and an href to the
   asserting row.
4. **Near matches note.** When the count is 0 and the plain box held two or more words, the summary adds "the plain box
   matches words in any order, so a reversed name is already an exact match; use the name fields to see reversed
   names apart".

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (41.5 s).
- `python -m products.board check`: green against live pub (about 25 s). New picture case: the known donor's graph, a
  donor row joined by `name-only@1`, and the "smith" name search's graph (87 nodes, 76 lines). On each it checks that
  no two labels or numbers share coordinates or have boxes that meet, that no rule id or "links rule" appears outside a
  `<title>`, and that the links' words are on the page.
- Slow tests (`-m slow`, 8, one new): green. The new one holds every `pub.links` rule to `RULE_WORDS` (14 of 14).
- Each new test was broken in memory and failed: placement off (pure tests and the check, 111 meetings), pairs not
  merged, causes not in key order, the build writing the raw id (the check), unknown ids hidden, the note dropped, an
  id missing from the table (slow test). Placement off left the check green until the crowded case was added (lesson).
- Screenshot of the "smith" graph checked (scratch): no text over text. 21 of 76 numbers and 9 of 87 node labels had
  no room; they are in the list and the tooltips.

## For the integrator

1. Copy this file into `inbox/merge-requests/` (the session's fence refused the link).
2. Merge, then **restart `qv4-board`** at the release (expected: graph.py, catalogue.py, panes.py changed). No table,
   unit or other module changes; no `state` run.
3. **Rebuild `lessons/INDEX.md` at the merge** (`bin/lessons-index`): one new lesson. No card, so `docs/board.md` is
   unchanged.

Lesson filed (above).

## Result (integrator, 25 October 17:40 NZDT)

Merged as 0aa2e6c: fast tier green (627 s), gate green, nothing to load.
Moved from the session's scratch folder into the inbox by the integrator.
Working copy and branches retired; release copy moved; `qv4-board`
restarted; a graph on the live board shows numbered edges, the list under
the key, and no rule id outside a title. The name-order fix (ruling 85)
launched from this main.
