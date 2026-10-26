A count carried on each result row (`count(*) over ()`) vanishes when the filter leaves no row: left-join the limited rows to a one-row counts CTE so "n hidden" is still said when every match was hidden.
area: products, the board, any search that filters rows and says how many it left out
paid-for-by: 2026-10-26, fix-products-board-1 (ruling 93)

The board's search returns each view's total as a window column on every
row. Ruling 93 hides removed companies and says how many were hidden;
done as a second window column, a search whose matches were all removed
returns nothing, and the register reads "none found" with no hidden count.
The fix, in one scan: `with m as (select *, <removed> as _removed from …
where …), h as (select count(*) filter (where not _removed) as total,
count(*) filter (where _removed) as hidden from m) select s.*, h.total,
h.hidden from h left join lateral (select * from m where not _removed
order by … limit %s) s on true`. The one row with no key carries the
counts and the caller drops it. The filter stays in the SQL before the
limit, never in Python after it, or a page of 50 shows 12.
