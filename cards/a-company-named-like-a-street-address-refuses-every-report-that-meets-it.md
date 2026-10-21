# A company named like a street address makes the shape refuse every report that meets it
kind: finding
state: closed
use-case: subject report (5.1); 7 construction; every template
session: construction-1
opened: 2026-10-21
closed: 2026-10-21

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

Closed 2026-10-21 by the report session (report-3). Rule 7 (`rules.py`)
now masks a company's own registered name before it reads a line for an
address by shape: the title of an organisation row, the title of the row a
line sits on (a role's company, a society, a return), and any name column
whose value ends in a company's legal ending (Limited, Ltd, Tāpui
(Limited), Incorporated). A company named "1 SHEA TERRACE LIMITED" is
shown as the register names it (hard limit 15 shows a company's registered
address); a person's name column that reads as a street, and an address
anywhere else in a statement, are refused as before (the fixture test
plants both). Measured: `companies:companies/9429047097209` and the
construction checkpoint's director are no longer refused; `python -m
products.report check` takes the first company named with a street number
and street word that has a director, from the tables at run time, and
fails if its report or its director's is refused on rule 7.
