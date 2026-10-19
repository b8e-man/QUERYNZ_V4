# The Gazette lane reads only the celebrant lists so far
kind: finding
state: open
use-case: 1
session: gazette
opened: 2026-10-20

Every one of the 207,133 notices is held and typed by the Gazette's own
section code, and one format is read: the Registrar-General's celebrant
lists (2,975 notices, 123,187 rows). The spec's other three kinds are typed
and not read. Their sizes, in notices, measured on the export: liquidator
appointed (`al`) 43,587; winding-up applications (`aw`) 30,452;
liquidation and removal (`ds`) 29,783; receivership (`ar`) 5,012;
bankruptcy (`ba`) 2,239; director prohibitions (`ot`, titled "Notice
prohibiting person from…") about 504; public appointments (`go`/`vr`
"Appointment of…") about 7,200 by the old classifier. Bankruptcy and
prohibition notices print home addresses: their readers keep the address
in `gazette_private` from the first line, and samples are masked.

Next session: read the prohibitions (one fixed template, small) and the
liquidator appointments (the largest), each its own profile and tranche.
