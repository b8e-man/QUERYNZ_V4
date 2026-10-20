# A liquidated company's registered office from before its liquidation is not published
kind: finding
state: open
use-case: 7 construction and phoenix detection; also 5, 12
session: construction-1
opened: 2026-10-21

The phoenix signature by place is a failed company and a new one at the
office the failed one traded from. `pub.company_addresses` keeps a
company's current registered office, and an earlier one only if it left
the file after July 2026 (11,788 rows `in_latest` false). On liquidation
the office moves to the liquidator's: measured 2026-10-21, 4,735 of the
4,945 companies in liquidation with an office in the file have one that
started within thirty days before their liquidator's appointment or later.
So the office a failed firm traded from is almost never held, and the
construction template's office check compares only what is (an office
dated before the failure) and is otherwise blocked, never clear. For the
companies lane: the change history's address table (kept since 16 August
2026; the 16 tables are unread, `the-companies-file-holds-no-past-directorships`)
published as dated past offices; before 16 August 2026 the old estate's
`bulk.company_addresses_history`, if it holds any, is the only source.
