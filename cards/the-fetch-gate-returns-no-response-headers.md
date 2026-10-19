# The fetch gate returns no response headers, so an ETag cannot be kept
kind: finding
state: open
use-case: -
session: societies
opened: 2026-10-20

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
