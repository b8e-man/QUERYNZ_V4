# The walk counts the companies at a registered office and does not list them
kind: finding
state: closed
use-case: 7 construction and phoenix detection; also 2, 13
session: construction-1
opened: 2026-10-21
closed: 2026-10-21

`walk.address_hub` counts the companies whose registered office in the
latest file is the same line and postcode, to flag a busy (50) or a
thousand-company address, and lists none of them. The phoenix signature by
place ("a failed company at the new firm's office") therefore cannot be
read when the two share neither a name nor a person: the construction
template's `shared-office` and the office half of `phoenix-signature` are
blocked, never clear, on every report. For the report lane: when the
office is not a hub (under 50 companies), list the other companies at it as
near rows with their status and registration date ("shares the registered
office; an office is not a person"), within the walk's limits; or let a
template ask for it as a setting. A template then reads them (a fix in its
folder). Weigh it with
`a-liquidated-companys-office-before-its-liquidation-is-not-published`:
the failed side's office is mostly its liquidator's.

Closed 2026-10-21 by the report session (report-3). When a section of the
template names the `office` bucket in its `sources`, the walk lists the
other companies whose registered office in the latest file is the start
company's (`walk.office_companies`), near, "shares the registered office
with the subject; an office is not a person, and a shared office is no
connection on its own", each with its status and registration date, via
the office row; twenty at most, the count of the rest in the memo. When
the office is a hub (fifty companies or more) none is listed and the memo
says how many share it, beside the busy or thousand-address flag. Measured
on NIRVANA FARM LIMITED: 20 of the companies at its office listed (TOROA
ASSETS LIMITED in receivership, SCARBRO BUILD LIMITED in liquidation among
them), the rest counted. `python -m products.report check` finds an office
shared by two to forty-nine companies among the first thirty shared
offices, taken from the tables at run time, and fails unless the others
are listed near with the reason and the walk's count matches the view's.
The construction template names `office` in its sources and reads the rows
for `shared-office` (a fix in its folder); the weight the card gives
`a-liquidated-companys-office-before-its-liquidation-is-not-published`
stands: the failed side's office is mostly its liquidator's.
