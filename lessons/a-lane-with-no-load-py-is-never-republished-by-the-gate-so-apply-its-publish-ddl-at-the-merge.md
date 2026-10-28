A lane with no load.py (links, built by a job) is never republished by the gate's staging or by its build job: a change to its publish.sql reaches the live pub views only when the integrator applies the lane's publish DDL at the merge.
area: integrator, merge gate, staging, links, published views
paid-for-by: 2026-10-28, links-3 (pub.links.relation absent live for five hours; board-10 read the relation from the evidence instead)

Rule: when a merge request changes a `publish.sql` in a module the gate
reports as "no touched module carries a load.py; nothing to load", run the
lane's publish DDL on the live database at the release (for links:
`links.publish_ddl()` through the owner login; CREATE OR REPLACE VIEW,
nothing dropped), then confirm the new column is in `pub`. The build job
rebuilds the lane's tables and does not re-create the views.

Why: `support/staging` publishes a lane by running its load.py into a
staging schema and swapping; the links lane has build.py and a job, so the
step skips it, and `qv4-links-build` added `relation` to `links.links`
without touching `pub.links`. The board session that followed had to read
the relation out of the evidence JSON.
