Count a row once across all its name columns when counting how often a name is filed: grouping per name column counted a candidate with two name columns twice, so the near-names pane said 3 rows where the search found 2.
area: products, the board, any count of names over views that declare more than one Name
paid-for-by: 2026-10-26, board-6 (ruling 92 (4))

The near-names pane counts, for each given name filed with a surname, the
rows that carry it. The first cut ran one `group by` per Name a view
declares. `pub.candidates` declares two Names, `name` (the Commission's
"SURNAME, Given") and `display_name`, and both hold the same person. So one
candidate row was counted once for each column, and "gary payinda" read 3
rows while the search beside it showed 2. The fix groups by every Name's
expression of a view together, takes the union of given words across them
per group, and adds the group's count once. Hold a count shown beside a
search to what that search finds, on live rows, before trusting it.
