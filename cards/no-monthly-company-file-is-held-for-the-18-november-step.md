# No monthly company file is held, and no director residential address is in any old table
kind: finding
state: open
use-case: step 4.3, "Hold the director addresses from before 18 November"
session: companies
opened: 2026-10-20

Step 4.3 asks to confirm the last monthly company file before 18 November
is in the document store, on both boxes and off site. Measured 20 October
2026: no raw package is on either box (the old runbook deleted each after
loading: `data-layer/nzbn_canonical/docs/bulk-import.md`); the old loader
never read an address from `companies_director.csv`; and no table in
`nzbn_canonical` holds a director's residential address except
`bulk.director_addresses`, about a dozen rows from the NZBN API (not read
by this lane). The sealed archive of 21 August
(`var/sealed/2026-08-21T210406Z/`) holds the company address tables only.

So the lane's export (four parts, pinned in `registers/companies/capture.py`)
is what is held of the July and August files, and it carries no
residential address. Whether the package's director file has an address
column at all is not known from here: no copy survives to look at. For
whichever session takes step 4.3.
