Date a company's failure from the first appointment a Gazette notice dates (a liquidator, a receiver, an administrator), never from the earliest insolvency notice: a winding-up application can be dismissed, and taken as the failure it moves the date years early and changes whose role was on the board at the time.
area: subject reports, products/templates, step 5.2 templates, flags, gazette, insolvency dates
paid-for-by: 2026-10-21, insurance-1 session, step 5.2 (template 06)

The insurance template's `sister-company-failure` set a company's failure
date beside each person's own role on it. Its first draft took the earliest
insolvency notice on the company. On the checkpoint, LJ GROUP NEW ZEALAND
LIMITED had a winding-up application published in February 2019 and a
liquidator appointed by the court on 31 May 2022: the flag dated the
failure to 2019, three years before the liquidation. A director appointed
between the two would have been read as "on the board at the failure" when
they joined a company that was still trading. The fix: rank the notices,
appointments first (`gazette_liquidations`, or a company notice whose
`event_basis` is "appointment"), the earliest of those; an application or a
creditors' notice dates the failure only where no appointment is held. A
fixture with an application a year before the person's appointment, and a
mutant that drops the ranking, hold it.
