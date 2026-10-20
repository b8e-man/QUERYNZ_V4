# The walk counts the companies at a registered office and does not list them
kind: finding
state: open
use-case: 7 construction and phoenix detection; also 2, 13
session: construction-1
opened: 2026-10-21

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
