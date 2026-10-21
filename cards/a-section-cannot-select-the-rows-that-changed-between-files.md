# A section cannot select only the rows that changed between the monthly files
kind: finding
state: closed
use-case: 5 business credit and monitoring
session: credit-1
opened: 2026-10-21
closed: 2026-10-21

The credit template's "what changed" wants the directors, holders and
registered offices that arrived or left between two monthly files, newest
first. A section selects rows by view and walk bucket only, and sorts by a
row's own start date, so its changes section lists every director, holder
and office of the entity with the files that show it (current and gone,
undated holdings last), and the dated change list itself is carried in the
flag `monthly-changes`. For the report lane: a section setting that keeps
only rows whose file window does not span the files held (`changed = true`:
`first_file` after the first file held, or `last_file` before the latest),
ordered by the file that first shows the change, newest first; the rows
left go on to the next section naming the view. Weigh it with
construction-1's `a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples`.

Closed 2026-10-21 by the report session (report-3). A section may say
`changed = true`: it keeps only the rows that arrived after the first
monthly file held (`first_file` later than it), left before the latest
(`in_latest` false), or are a company's earlier state (`company_states`),
each marked with the file that first shows the change (`changed_in`,
printed "change first shown in the file …"), ordered by that file newest
first, confirmed before near; every other row goes on to the next section
naming its view. The files held are read from pub.companies once an hour
(the lane publishes no list; its card stands). Measured: `python -m
products.report check` builds the first company with an earlier state
under a template whose first section is `changed = true` and fails unless
the state is kept with its file and no unchanged row is; a fixture test
holds the filter on a canned walk. The credit template's "what changed"
section sets it (a fix in its folder).
