When a `pub.names` read hangs or a links arm turns red, count `pub.links` by grade and read one row by key before changing a check: a links rebuild locks `links.rows` and republishes in steps (near held 3,010 of 477,172).
area: board, links, checks
paid-for-by: board-9, 28 October 2026

Why: on 28 October the links-3 merge rebuilt the lane while board-9 measured. A query by key on `pub.names` waited on a lock for about twenty minutes (even an EXPLAIN timed out, which is a lock and not a plan); `pub.groups` answered throughout. Afterwards item 22 said the "smith" graph drew no near line, and the merged board's own code said the same, because the near grade was not yet republished; the session gave item 22 a fallback case before it counted the grades again and saw them back. The fallback is harmless and kept, but its first comment blamed the data.

How to apply: a statement on a `pub` view of the links lane that times out with no plan is a lock: poll a read by key until it answers, do not rewrite the query. A red that also shows on the main checkout's code is not your branch's; run `select grade, count(*) from pub.links group by 1` and compare with the last merge's figures before you touch the arm.
