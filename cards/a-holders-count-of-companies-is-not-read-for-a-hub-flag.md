# A holder of record's count of companies is not read, so a holding hub is flagged only by its name
kind: finding
state: open
use-case: subject report (5.1); 13 beneficial ownership and AML
session: ownership-1
opened: 2026-10-21

The walk flags a professional director by its group's directorships and a
holder only when its name says nominee, trustee, custodian or the Crown.
How many companies a holder of record holds is never counted, so a
custodian or trustee company named otherwise is not a hub: WYNDHAM
SECURITIES LIMITED holds shares in 630 companies in the latest file, GYW
MASTER TRUST LIMITED in 308. Measured 21 October: no holder holds a
thousand (the largest, NEW ZEALAND TRUSTEE SERVICES LIMITED, 659); eleven
company holders hold 200 or more. For the report lane: a holder-count
hub like `busy_address`, counted on the holder's name for a company
holder (no key exists) and on its group for a person, with a setting for
the threshold (the plan's thousand; fifty, as for directors and offices,
is what the data reaches). The ownership template's `holder-hubs` is
blocked, never clear, until then.
