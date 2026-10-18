# The release's search gate reads the product on 8300, so querynz-pi-web is in the carve-out
kind: finding
state: closed
use-case: 1
session: founding-f05585e
opened: 2026-10-18
closed: 2026-10-18

Batch 2 of 1.4 stopped and disabled `querynz-pi-web` at 11:35 on 18
October as one of the "old apps". On Arthur's word the earlier founding
session ran the release by hand at 12:36 instead of waiting for the 19
October 06:15 run. It went red at 12:45: `pi_search_gate` reported
"connection refused". Nothing was deployed or flipped. The gate's `--base`
default is `http://127.0.0.1:8300`, which is `pi.app` under
`querynz-pi-web`, the product's own instance; the gate serves the snapshot
on an ephemeral port and checks that the browser search finds every hit the
server's search finds. Under 1.4 item 7 the unit was enabled and started
again at 12:5x. The release run again by hand was green: `2026-10-18T1334`
published at 13:46. Compared with `2026-10-18T0617` it is inside the
yardstick in `docs/baseline.md`: only the stamp keys moved in the data
kinds, `data/cite` had no churn at all (the derive chain is off, which is
the ruling's intent), and nothing static changed.

Every address the release opens, traced from `ops/pi_release.py` and each
gate it names: the publisher on 8301 (the generator, the snapshot gate, the
eleven served gates, the before-and-after compare); the product on 8300
(the search gate alone); the database, through the publisher's own
connection; an ephemeral local server of the snapshot (landing and search
gates); Cloudflare for the deploy. The gui build is `tsc` and `vite build`;
its proxy to 8300 is the dev server's and plays no part in a build. No
other batch 2 unit is addressed: `querynz-api` on 8100 appears only in the
dev-server proxy of the console build; precompute, the feeds, the images,
`querynz-ec-results`, `robots-audit`, the reference downloads,
`querynz-llm@1` and `querynz-embed` are reached by nothing the release runs.

Moved: `CARVE_OUT` in `.claude/hooks/fence.py` (the hook now refuses to
stop it), the stop list, the two tables in 1.4 of the plan (the baseline's
carve-out table already had it, "because the publisher is its twin"; the
plan now agrees), `docs/status.md`. A queue item offers the alternative, a
one-line change to the gate's default in the old repository, with the
default being to leave the unit running.
