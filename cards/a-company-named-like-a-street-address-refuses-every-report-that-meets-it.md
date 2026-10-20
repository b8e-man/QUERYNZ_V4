# A company named like a street address makes the shape refuse every report that meets it
kind: finding
state: open
use-case: subject report (5.1); 7 construction; every template
session: construction-1
opened: 2026-10-21

The shape's presentation rule 7 reads a row's values for an address by its
shape (a street number before a street word) everywhere but
`company_addresses`. A company whose legal name is a street address trips
it: at the construction checkpoint a person's walk met a company named "1
SHEA TERRACE LIMITED" (`companies:companies/9429047097209`) and the whole
report was REFUSED, though the name is the register's and a company's name
is not a home address. Measured 2026-10-21: 2,914 companies in
`pub.companies` (1,454 registered) have a name of that shape, many of them
property companies, so any template whose walk reaches one is refused. For
the report lane: exempt a company's own name (the `companies` title, and the
`entity_title` a role carries) from rule 7, as the registered office is,
while still reading a person's name column; a test with a company of that
name on a director's walk. Checkpoint subject 7 of
`products/templates/07-construction/checkpoint.list`.
