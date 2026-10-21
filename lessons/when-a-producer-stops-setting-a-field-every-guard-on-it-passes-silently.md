When a shared producer stops setting a field, every consumer's guard on that field passes silently, and its tests, built on the old shape, stay green; grep the consumers and give each guard a test in the new shape, seen failing first.
area: capture, fetch gate, redirects, tests, checks that silently pass
paid-for-by: 2026-10-22, redirects-1 (card six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect)

The gate stopped following redirects and began returning `final_url` equal
to the URL asked, with the 3xx's target in `Fetched.location`. Six lanes
stopped "on a redirect to another host" by testing `final_url`, so the stop
could no longer fire; four of them had tests injecting a `Fetched` with
`final_url` elsewhere, a shape the gate no longer produces, and all four
stayed green. Each guard now reads `location`, and each test injects a 302
with a Location elsewhere, run once against the old guard to see it fail.
