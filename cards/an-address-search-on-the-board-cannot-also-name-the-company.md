# An address search on the board cannot also name the company
kind: finding
state: open
use-case: the board (4.9), the field search (ruling 82)
session: board-3
opened: 2026-10-25

The field search joins its fields with "and" inside one view. A company's
registered office is in `pub.company_addresses`, which carries the
company's key but not its name, so an address and an organisation filled
together find no registered office: the address view has no organisation
column, and `companies` has no address. The same holds for a person's
name with any address (no person's view has an address, by hard limit 15,
which is right). Charities and limited partnerships carry both and are
found.

Two ways to close it, both the board's alone: declare a join in
`catalogue.Fields` (an organisation field on `company_addresses` matched
through `entity_key` to `companies.name`), or let the field search match
a parent's name where a view has a `parent`. Either is one tranche with a
live test ("a known company found by its name and its office"). Until
then the results pane says "none of its views holds a column for" the
field, so the gap is stated, not silent.

A smaller limit found in the same work: 49 director rows have no
`last_name` part and 22 no `first_name` (of 1,185,805), so the name fields,
which read the parts where a register prints them, do not find those rows;
the plain box still does.
