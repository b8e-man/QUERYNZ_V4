# A Gazette company notice is shown with one bare date that may be a hearing day
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`catalogue.py` dates `gazette_company_notices` by `event_on`. For a
winding-up application that is the day it is to be heard: notice
`2018-aw3107` (KELSTWORURAL LIMITED) was filed 25 May 2018 and published
5 July 2018, and the memo shows only "(13 July 2018)", read against the
notice's text at the recruitment checkpoint. A reader takes it for the day
of the liquidation. For the report lane: say what the date is ("to be heard
13 July 2018; published 5 July 2018"), from the kind of notice.

Closed 2026-10-20 by the report session (report-2). The catalogue now
carries what a date is: `gazette_company_notices` is dated by `event_on`
with the lane's `event_basis` saying what it dates (hearing → "to be
heard", objections by, appointment → "appointed", ceased to act, meeting,
claims by, dividend), and the filing day and the publication day are
printed beside it; a notice with no event day is dated by its publication
day rather than marked undated; a liquidation's `appointed_on` reads
"appointed". The card's notice now prints "(to be heard 13 July 2018; filed
25 May 2018; published 5 July 2018)" on `companies:companies/9429031200745`.
Measured: `python -m products.report check` builds a report on the company
of the latest winding-up notice with a hearing, filing and publication day,
taken from the tables at run time, and fails unless the notice's dating
text says all three.
