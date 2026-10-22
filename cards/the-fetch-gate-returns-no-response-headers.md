# The fetch gate returns no response headers, so an ETag cannot be kept
kind: finding
state: closed
use-case: -
session: societies
opened: 2026-10-20
closed: 2026-10-23

`support/fetchgate.open_url` returns status, body and final URL only. The
NZBN API asks callers to keep each answer's `ETag` and send it back in
`If-None-Match`, so an unchanged entity answers 304 with no body
(`portal.api.business.govt.nz/api/nzbn`, read 20 October 2026). Without the
header the societies lane asks each society once a week and lands the
answer by hash, so an unchanged answer is stored once but still sent.

Fix (support/fetchgate, a fix session): return the response headers on
`Fetched` (and treat 304 as "unchanged", not a block). The lane then keeps
the ETag on its ask row and sends it. Sits beside the open card on the
gate's redirects and gzip.

Closed 2026-10-23 by the fix session fix-support-fetchgate-1. `Fetched` has a
new last field, `headers`: a plain dict, names as the host sent them, empty
by default, so every caller that builds one positionally still works.
`open_url` fills it from the answer it returns. `Fetched.unchanged` is true on
a 304, and `open_url` returns a 304 with an empty body and never calls it a
block. A lane keeps `headers["ETag"]` and passes `headers={"If-None-Match":
etag}` to `open_url`. Test: a loopback server answers 200 with an ETag, then
304 when the ETag comes back; that read is `unchanged`, has no body, is not
blocked and carries the ETag. No lane changed: keeping the ETag on the
societies lane's ask row is that lane's own fix.
