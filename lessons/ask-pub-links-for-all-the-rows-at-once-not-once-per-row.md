Ask `pub.links` for every row in hand at once (`row_a = any(%s) or row_b = any(%s)`), never per row or through a lateral join: the view's latest-decision step (a DISTINCT ON over all of `links.decisions`) runs again for each row.
area: board, links, pub views, query cost
paid-for-by: board-8, 28 October 2026

Why: board-8 (ruling 105) first read the near links one hop from a search's rows with a lateral join, one probe per row. EXPLAIN ANALYZE on live data showed the index probes on `links.links` cost 0.5 ms a row, but the view's `last_decision` subquery sorted all 5,694 decisions again for every row: 501 ms for 40 rows. One query with the row keys as an array, the per-row cap taken by a window (`row_number() over (partition by …)`), read 120 rows' near links in 102 ms, cold.

How to apply: when a product or a pane needs `pub.links` (or any `pub` view built on a DISTINCT ON or an aggregate) for several rows, pass the keys as one array and cap in the same statement. Check the plan for `loops=` on the view's inner step before you trust a per-row read. The board's older `links_view.links_of` still asks once per row; it costs the rows graph about 150 ms a search.
