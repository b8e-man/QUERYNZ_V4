# A section cannot set the start's own rows apart from those of the companies its people sit on
kind: finding
state: closed
use-case: 7 construction; also 2, 3, 4, 13
session: construction-1
opened: 2026-10-21
closed: 2026-10-21

The builder files a row in the first section naming its view and walk
bucket. Gazette notices on the start company and on a person's companies
come from one bucket (`pointing`), and every company reached is one view,
so a template cannot have "the Gazette on the entity itself" apart from
"the notices on the companies that share its people", nor "failed
companies" apart from "its people's going companies". Use case 7's brief
asks for both splits; the construction template lists every company in one
section (each with its status) and every notice in one ("on the entity
itself, and on the companies above"), and its flags do the splitting. For
the report lane: a section filter, `own = true|false` (the row sits on the
start, or not) and a status filter for companies, or the `order` setting of
`a-section-cannot-put-current-roles-first` widened to grouping.

Closed 2026-10-21 by the report session (report-3). A section takes three
filters in `template.toml`: `own = true` keeps the rows of the start itself
and the rows that sit on it or on its group (its directors, holders,
office, the notices on it), `own = false` keeps the rest (its people's
other companies, the notices on those, the companies at its office, the
chain above it); `statuses = [...]` keeps only rows whose `status` is one
of them (a company's; a row with no status column passes); `changed = true`
is `a-section-cannot-select-the-rows-that-changed-between-files`. A row one
section leaves goes on to the next that names its view, as before.
Measured: `python -m products.report check` builds a report on a company
whose director holds another directorship under a template with an
`own = true` section and an `own = false` one, and fails unless the first
holds the start's directors and nothing reached through them, and the
second the reverse; a fixture test holds the parsing and the three filters
on a canned walk. The construction template splits its Gazette and
companies sections with `own` and `statuses` (a fix in its folder).
