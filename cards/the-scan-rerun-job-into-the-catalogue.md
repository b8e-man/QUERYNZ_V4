# The scan's re-run job goes into the catalogue at the merge
kind: blocker
state: open
use-case: 9
session: scan-1
opened: 2026-10-21

Two edits outside the scan fence, for the integrator at the merge of
`scan-1`:

1. Create the scan's tables in the real database: `QV4_SCAN_STATE=querynz_v4/register_scan
   python -m products.scan state` (schema `register_scan` exists from
   step 1.8), then run both proving scans once:
   `python -m products.scan run society-officers-liquidations` and
   `python -m products.scan run donors-named-as-companies` (each takes
   seconds), and install and start `products/scan/units/qv4-scan.service`
   (port 8450, the local network).
2. Add `products/scan/jobs-proposed.toml` (`qv4-scan-rerun`: after the
   links' build, `python -m products.scan run --stale`) to
   `support/scheduler/jobs.toml`, run `python -m support.scheduler check`,
   and delete the proposed file. `memory_gb` is a first figure.
