# board: where it stands

**Date:** 2026-10-28. **Step:** 4.9 second version, rulings 80 to 110,
`products/board/`. **Session:** board-11 (ruling 110, the dossier).
**Merge request:** `board-11`.

## Done

- Rulings 80 to 108 and 106 (2): as before (board-8 to board-10).
- Ruling 110 (1): an entity result lists no "matching here" names; its
  count and registers stay.
- Ruling 110, `dossier.py`: one entity or lone row on one pane, from the
  published views and pub.groups, links, names, decisions alone. It shows
  the name, the names as filed with counts, a timeline of rows by register
  with role, body, dates, fields (flags) and citation, roles in date
  order, donations summed by year from the filed amounts the view adds
  (disclosures, replaced rows and blank amounts listed and not added),
  declared interests, related companies, near matches, contested and
  decisions, and the report link. A row in a group opens its group's
  dossier. A suppressed row is never gathered or named.
- It opens under the graph, beside the results or on the graph tab, on a
  result click or a node tap (`GET /dossier`, no reload). `d=` in the
  address reopens it and its graph. Without script there is a plain
  "dossier" link.
- Cost: largest group (1,220 rows) gather 0.10 s, pane 0.02 s, 0.9 MB;
  "Graeme Hart" groups 0.04 s, a lone donation row 0.03 s.
- Check item 25; `tests/test_dossier.py`; two live tests in `test_real.py`
  (one plants an added disclosure and turns item 25 red).

## Known limits

- No claims section: no claims lane publishes yet.
- `pub.mp_interests` is read by `member_return`, which the lane's table
  does not index (25k rows, a few ms).
- 32 registers share 14 colours (queue item `graph-node-colours-by-family`).

## Next

1. The integrator merges `session/board-11` and restarts `qv4-board` at
   the release. No table, unit or setting changes.
