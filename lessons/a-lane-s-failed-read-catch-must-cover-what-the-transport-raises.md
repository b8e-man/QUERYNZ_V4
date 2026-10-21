A lane that sorts failed reads by the gate's returned status must also catch what the transport raises (a socket timeout, a reset, a dropped connection), or one slow answer ends the whole night as a traceback.
area: capture, failed reads, fetch gate, nightly jobs, societies
paid-for-by: 2026-10-21, fix-registers-societies-1, card the-societies-capture-dies-on-one-read-timeout

`fetchgate.open_url` returns a `Fetched` for every HTTP answer, a 4xx or 5xx
included, so a lane's loop looked complete when it handled `got.blocked`.
But a timeout or a reset never becomes an answer: urllib raises it, and the
lane's loop has no `except`. The societies night died after three hours on
one `TimeoutError`. Catch `TimeoutError`, `ConnectionError`,
`http.client.IncompleteRead` and a `URLError` wrapping them; set the item
aside with the reason; rest; stop after a run of them. Test with an invented
fetcher that raises, not only one that returns a bad status.
