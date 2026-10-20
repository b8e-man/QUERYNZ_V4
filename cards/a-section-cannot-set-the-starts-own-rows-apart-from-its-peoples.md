# A section cannot set the start's own rows apart from those of the companies its people sit on
kind: finding
state: open
use-case: 7 construction; also 2, 3, 4, 13
session: construction-1
opened: 2026-10-21

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
