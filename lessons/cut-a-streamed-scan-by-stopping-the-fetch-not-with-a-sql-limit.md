Cut a streamed scan by stopping the fetch, never with a SQL `limit`: the limit changed the plan, and a 40-line cut took 46 s where the whole 854-line run took 3 s.
area: products/scan, queries over pub, tests against the real tables
paid-for-by: 2026-10-21, scan-1, step 6.1

The runner streams a scan's one query through a server-side cursor in
pages. For a test it was cut with `limit %s` in the SQL, and the planner
turned the join into one that found the first rows slowly: 46 s for 40
lines, two minutes for the slow test, where the full runs took 1 to 3 s.
Fetching the full query's cursor and stopping after N rows keeps the plan
the full run gets, and the slow test fell to 9 s. A time measured on a cut
run says nothing about the whole; measure the whole.
