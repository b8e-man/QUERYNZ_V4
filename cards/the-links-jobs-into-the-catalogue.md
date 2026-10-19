# The links jobs into the catalogue
kind: blocker
state: open
use-case: -
session: links
opened: 2026-10-20
closed:

`support/scheduler/jobs.toml` is the integrator's. `links/jobs-proposed.toml`
carries two entries for it: `qv4-links-build` (rows, links, watch, groups,
test pairs, measurements after each lane load; `python -m links.build_all`)
and `qv4-links-review` (the review agent's reading on the review profile;
`python -m links.review --run <sample>`). Neither is queued by the links
session. At the merge: append both, run the catalogue's `check`, and delete
the proposed file. The links build in the gate's staging step is the same
command with `--schema links`; the old ledgers are copied once with
`python -m links.old --schema links` before it (its mapping needs the rows).
