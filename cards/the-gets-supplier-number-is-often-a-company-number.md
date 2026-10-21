# The GETS supplier number is often a Companies Office company number
kind: finding
state: open
use-case: 10 tender and award intelligence; 9 government procurement integrity
session: scan-templates-1
opened: 2026-10-21

`pub.award_suppliers.nzbn_as_published` holds no valid NZBN, but its short
values are mostly company numbers. Measured 21 October 2026 against
`pub.companies.number` (in the latest file): 5 digits 29 rows, 29 hit; 6
digits 389, 388 hit; 7 digits 637, 615 hit; 8 to 11 digits, none. Of the
1,032 hits, 869 agree with the supplier's name on a crude test (the first
six letters). So about a thousand awards could be joined to their company
by an official number rather than by name alone.

The scan templates do not use it (the brief: business number only). A
number published unvalidated in a field the ministry calls the NZBN is a
hint, not a key, until a rule says so. Owner: links (a rule `company-number`
on the award suppliers, number and name together, graded by the agreement)
or the tenders lane (classify the shape as "company number" beside
`nzbn_form`). Then `tender-awards` takes it as `number = [...]` with no
other change.
