# A screen started from a donation row has no group, so it cannot clear
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

A donation, loan or disclosure row is kind "figure" in the catalogue, so
the walk gives it no group ("an organisation needs no group") even when it
names a person and a confirmed link joins it to a director row
(`party_returns:d87ba315…/A/10` → a director of G233 TRUSTEE LIMITED). The
links and companies of that director row are not walked. The recruitment
template blocks its prohibition, liquidation and removal checks on such a
start and tells the reader to start from a person row. For the report
lane: take the group of the person row a confirmed link names, when the
start is a figure row.

Closed 2026-10-20 by the report session (report-2). A start that is a filed
row (a donation, a loan, a disclosure, an interest line) now takes the group
of the person row a confirmed link names (`walk.adopted_group`: the first
by ref when several, with the count of groups those rows fall in stated);
with no such link it says there is no group to take. The walk then runs as
a person's: the group's rows, their companies and links, one step further
as near. The group line and the group-standing flag both say the group is
an adopted one and name the row it came from. The card's own row
`party_returns:d87ba315…/A/10` now walks the director's group of 46 rows.
Measured: `python -m products.report check` builds a report on a donation
row confirmed to a grouped director row, taken from the tables at run
time, and fails unless the group is taken and the flag says so. The
recruitment template's "start from a person row" block can be lifted (a
fix in its folder) once its own tests have seen a figure start clear.
