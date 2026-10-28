# The links lane joins no charity officer to any other row and no charity to its company, so the report reaches them by name and by number itself
kind: finding
state: open
use-case: 11 healthcare operator governance; 12 property; 2, 8, 9, 14; every template reading the Charities Register
session: fix-report-2
opened: 2026-10-21

`pub.names` carries no `charity_officers` row and `pub.links` no link to a
`charities:` ref (measured 2026-10-21: 0 of either). So a director and a
trustee of the same full name are in no common group, and a charity is not
joined to its companies-register row. The report shape (fix-report-2)
bridges it meanwhile: a company's charity by `nzbn` as an entity of the walk
(confirmed, rule `official-number`), and a charity officer carrying a
person's name (a director, society officer, member, candidate, interests
return, promoter's person or appointee) listed near by name with the reason
"no link joins the Charities Register's officers to any other row yet"
(`walk.NAME_JOIN_TO`, `walk.NUMBER_JOINS`). Those are stopgaps: a by-name
match is a namesake until a rule confirms it, and a charity officer start
reaches nothing of the person's other rows.

For the links lane, as `the-report-cannot-reach-the-charities-register`
item 2 asked: `charity_officers` (kind person, 585,837 rows, 0 suppressed)
into `pub.names`, so `full-name@1` and the other person rules join them;
and a charity's `nzbn` or `incorporation_number` joined to its
companies-register or societies row as `official-number@1`, confirmed. When
both land, the shape's `NAME_JOIN_TO` entry for `charity_officers` comes
out (a fix in `products/report/walk.py`) and the number join may stay or
go; the charities section's text in the subject template changes with it.

2026-10-28, fix-products-report-1: since ruling 114's links build joins
charity officers, `python -m products.report check` reports one problem on
main as on this branch: for one director, "a charity officer of the
director's name is listed by neither name nor the person's own charity".
The walk's charity bridge (`walk.NAME_JOIN_TO`, "no link joins the
Charities Register's officers") was written before that build and no longer
describes it. To fix: retire the bridge for charity officers now that the
links lane joins them, and change the check to expect the joined rows.
