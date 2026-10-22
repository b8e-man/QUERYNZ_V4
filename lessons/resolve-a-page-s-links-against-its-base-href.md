Resolve a captured page's relative links against its own `<base href>`, and percent-encode them, before asking: 27 council register files answered 404 and three hosts were held for links the code had built wrong.
area: capture, links, fetchgate, councillor_interests

Why: Hastings' and Wairoa's register pages link each member's file as `assets/…` under `<base href="/">`. Joined to
the page's own path they became addresses the site does not have: 27 404s on the first night. Three other councils
link files by names with spaces, line breaks or macrons; urllib refused them before sending, and the capture took the
transport error for a host in trouble and held the host.

How to apply: a link finder reads `<base href>` first, joins against it, strips control characters and
percent-encodes the path; a request that never left the box (ValueError, UnicodeError) is recorded as not sent, is not
an ask, and never holds a host. Before trusting a run's 404s, mask a few of the failed addresses to their shape and
compare them with the page's own hrefs.
