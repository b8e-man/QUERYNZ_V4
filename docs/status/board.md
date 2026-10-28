# board: where it stands

**Date:** 2026-10-28. **Step:** 4.9 second version, rulings 80 to 108,
`products/board/`. **Session:** board-9 (ruling 108, the results pane).
**Merge request:** `board-9`.

## Done

- Rulings 80 to 105: as before (board-8: the graph's entity state).
- Ruling 108, the search tab's results pane:
  1. The rows and entities switch sits above the results too
     (`g=entities`). In entities, the entities come first: name, "n rows,
     n registers", contested, registers named. The rows in no group come
     after, as rows. A suppressed row is never gathered.
  2. One tab per field matched, for the search box alone and for "any
     field may match": first, middle and last name, address,
     organisation, year, number, and "elsewhere in the row". Each tab
     shows its count, with registers closed to name and count. "All
     fields must match" keeps the one list. One query per view.
  3. Entity search: the box or the name fields are matched against
     `pub.names`' indexed keys (equality only), then folded into
     `pub.groups`.
  4. Clicking a result opens the graph to the right, centred on it, in
     the current state. A narrow window stacks it underneath. No new
     content-security source.
- The search's scans are queued longest first, from each view's last time.
- Words for links-3's three new rules.
- Cost, live and under load (load average 5 to 9): "hart" search 1.95 s,
  1.93 s with tabs; "smith" 2.10 s and 2.11 s. Gathering the entities
  adds 0.17 to 0.19 s; the entity search's lookup takes 1 to 48 ms ("John Smith": 37 groups). The
  whole page went from 2.07 s to 2.18 s for "hart" (2.34 s in entities)
  and from 2.21 s to 2.72 s for "smith" (2.46 s in entities). Pages grow
  from 0.9 MB to 1.5 MB and from 1.8 MB to 2.8 MB, because a row is
  repeated under each tab it matched.
- Check item 23; `tests/test_results.py`; two live tests. The check,
  test_real, test_night, test_canvas and the fast tier are all green.

## Known limits

- The links lane's "related" grade (successor-name, ruling 106 (2)) is
  not drawn: the lineage frame is still owed.
- No suppressed row live sits in a group. The gathering case is held on
  a fixture; the live check covers the pane.
- A last name alone, or a first name alone, sits on no index of
  `pub.names`, so it finds entities only through the rows shown.
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).

## Next

1. The integrator merges `session/board-9` and restarts `qv4-board` at
   the release. No table or unit changes.
