# No link reaches a Gazette bankruptcy, a Gazette appointment or a candidate's own return
kind: finding
state: open
use-case: 8 recruitment board screen; every subject report
session: recruitment
opened: 2026-10-20

`pub.names` carries no row of `gazette_bankruptcies` (65,299 notices),
`gazette_appointments`, `candidate_return_totals` or
`candidate_return_donors`, so no link rule joins them to a person and no
subject report can reach one. A board screen therefore cannot see a
bankruptcy: the recruitment template's bankruptcy check is blocked, never
clear, and its limits page says so. For links: carry them in `pub.names`
(an annulment's withholding kept) and let the two person rules run over
them. When they arrive, the recruitment template reads appointments again
and its bankruptcy rule clears where it can.
