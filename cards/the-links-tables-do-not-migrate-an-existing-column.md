# The links tables do not migrate an existing column
kind: finding
state: closed
use-case: 1
session: founding
opened: 2026-10-20
closed: 2026-10-20

`links/tables.sql` creates every table with `CREATE TABLE IF NOT EXISTS`.
The live `links.old_decisions` existed before links-1 with fewer columns
(the step 1 shape), so the first live load left it as it was and
`links.old` failed on `source`. The integrator added `source`, `verdict`
and `mapped_how` by hand (`ADD COLUMN IF NOT EXISTS`) on 20 October and
reran the copy. The register lanes carry such changes in their own
`tables.sql` (`party_returns` adds `year_from` and `party_key` that way).
Fix, the links lane's: an `ALTER TABLE … ADD COLUMN IF NOT EXISTS` line
per column added since a table first shipped, or a rebuild that drops its
own regenerable tables first (every links table is regenerable; the old
ledgers are copied again from the old database).

Closed by the review session (track C): `links/tables.sql` now carries an
`ALTER TABLE … ADD COLUMN IF NOT EXISTS` line for every column added after a
table first shipped (`old_decisions`: `source`, `verdict`, `mapped_how`;
`readings`: the scoring columns), and a test holds that each column in a
CREATE TABLE added after links-1 has its ALTER line.
