Read a link from either end as a union of the two directions, never as `row_a = x or row_b = x`: the OR made a 133,000 by 2.8 million nested loop that ran past the ten-minute limit; the union ran in two minutes.
area: products, links, queries over pub.links
paid-for-by: 2026-10-21, scan-1, step 6.1

A scan's person step under the "direct" chains setting joined every
society officer to `pub.links` on `row_a = ref or row_b = ref`. The
planner cannot use an index on either column through an OR across two
columns, so it materialised the officers and walked every link for each
(EXPLAIN: a nested loop with a join filter, cost twenty million), and the
statement timed out at ten minutes. The same join written as
`join (select row_a as this, row_b as other, … from pub.links union all
select row_b, row_a, … from pub.links) l on l.this = ref` lets each branch
use its key index. The report's walk reads links by `= any(refs)` on a
handful of refs, where the OR is cheap; a scan reads them for a whole
register, where it is not.
