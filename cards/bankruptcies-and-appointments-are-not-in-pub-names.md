# No link reaches a Gazette bankruptcy, a Gazette appointment or a candidate's own return
kind: finding
state: closed
use-case: 8 recruitment board screen; every subject report
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`pub.names` carries no row of `gazette_bankruptcies` (65,299 notices),
`gazette_appointments`, `candidate_return_totals` or
`candidate_return_donors`, so no link rule joins them to a person and no
subject report can reach one. A board screen therefore cannot see a
bankruptcy: the recruitment template's bankruptcy check is blocked, never
clear, and its limits page says so. For links: carry them in `pub.names`
(an annulment's withholding kept) and let the two person rules run over
them. When they arrive, the recruitment template reads appointments again
and its bankruptcy rule clears where it can.

Links, 20 October (links-2). `pub.names` now carries `gazette_bankruptcies`
(64,741 rows; the 552 notices whose name the Gazette later withheld have no
name and make no row, so an annulment's withholding is kept),
`gazette_appointments` (3,155), `candidate_return_totals` (385) and
`candidate_return_donors` (175), and the two person rules run over them:
rule 1 joins 15,095 Gazette rows to Gazette rows and 18,274 to the companies
register (bankrupts among them); the watch flags 149 confirmed links where a
directorship was taken up within three years of the bankruptcy. The filing
candidates had been keyed with every given name in the first-and-last key
(lesson `the-given-name-is-the-first-given-name-…`), fixed. The recruitment
template may read appointments and bankruptcies again.
