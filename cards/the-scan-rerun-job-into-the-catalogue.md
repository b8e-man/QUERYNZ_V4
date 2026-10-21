# The scan's re-run job goes into the catalogue at the merge
kind: blocker
state: closed
use-case: 9
session: scan-1
opened: 2026-10-21
closed: 2026-10-21

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

Closed by the integrator at the merge of `scan-1` (21 October 2026, f8a697e) and recorded in the merge after it: `qv4-scan-rerun` in the catalogue at priority 59, class whenever (40 taken; the per-job environment is not a catalogue field and the product's defaults carry the same values), the proposed file removed; after the merge the scan's tables made in `querynz_v4.register_scan`, both proving scans run (854 and 287 lines, 0 problems), `qv4-scan.service` placed by the installer, enabled and started on port 8450.
