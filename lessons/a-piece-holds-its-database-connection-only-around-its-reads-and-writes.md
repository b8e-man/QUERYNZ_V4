A piece that calls the model holds its database connection only to read its input and to land its rows, never across the model's call, or a wide run fills the login's connection limit.
area: scheduler pieces, lanes, model readers, database logins
paid-for-by: 26 November 2026, the first qv4-news-read row on the 27B at 16 streams a box

registers.news.read opened `db.connect()` around the whole piece, so each of the 32 pieces in flight held the owner login (limit 40) for the 38 seconds the model read. The tests and any other job on that login were refused ("too many connections for role qv4_owner"); 14 scheduler tests failed on it and looked like a broken change. `piece(connect=...)` now opens a connection to read the article and another to land it. Any lane whose pieces run wide on a model should do the same; a red test run beside a wide job is checked for this before the code is blamed.
