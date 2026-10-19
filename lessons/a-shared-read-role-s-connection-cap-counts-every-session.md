A server that scans tables in parallel never pools the shared session reader, whose cap of five counts every session's bin/q: scan on a role of its own (the product reader), one shared connection per page, one page at a time.
area: products, servers, support/db, the board
paid-for-by: 2026-10-20, board session, step 4.9

The first board scanned the 35 published views on four pooled connections of
`qv4_read`; with the check's own connection and the page's that made six,
and the sixth was refused ("too many connections for role"), while every
other session's `bin/q` would have been refused too. `qv4_product` sees
`pub` alone, which is all a scan needs, and has a cap of ten. The page's
one `qv4_read` connection reads the document names and the board's own
state; a lock holds renders to one at a time.
