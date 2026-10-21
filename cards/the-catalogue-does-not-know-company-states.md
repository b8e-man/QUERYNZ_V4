# The report's catalogue does not know pub.company_states, so no template can show a status or name change between the monthly files
kind: finding
state: closed
use-case: 5 business credit and monitoring; also 3, 7, 13
session: credit-1
opened: 2026-10-21
closed: 2026-10-21

The companies lane publishes `pub.company_states`: the earlier state of each
entity a later monthly file changed (5,629 rows in `companies-2026-07`,
measured 2026-10-21: 3,979 status changes, such as Registered to In
Liquidation, and 1,346 name changes). `products/report/catalogue.py` has no
View for it, and a template that names an unknown view is refused when
loaded, so the credit template cannot list the change use case 5 asks for
first ("has anything changed"): it shows the status today and blocks
`status-name-changes`, and `monthly-changes` and `recent-adverse-change`
never clear (`STATES = False` in its rules). `the-catalogue-does-not-know-gazette-possessions`
mentions the view in passing; this card is the need. For the report lane: a
View (`kind="organisation"`, title `name`, `period=("file", "file")`,
`entity=("companies", "entity_key")`, a statement such as "{title}: {status}
in {file}"), and `("company_states", "entity_key", "file")` in
`walk.ROLES_ON["companies"]` so a company's earlier states are its own rows.
The template then reads it and sets `STATES = True` (a fix in its folder).

Closed 2026-10-21 by the report session (report-3). `catalogue.py` carries
`company_states` (register companies, an organisation row titled by its
name, sitting on its company; dated "as in the file companies-2026-07" by
a new `as_in` column kind, with the earlier state's registered and removed
days beside; the statement "…: an earlier state of …, registered …, as the
file … carried it; a later file changed it"; the note says the day of the
change is between two files' cuts the lane does not publish) and
`walk.ROLES_ON["companies"]` lists a company's earlier states as its own
rows. The shape's own template reads it in its companies section.
Measured: `python -m products.report check` takes the first company with
an earlier state, from the tables at run time, and fails unless the state
is listed dated by its file. The credit template reads it and sets
`STATES = True` (a fix in its folder).
