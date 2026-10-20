# The catalogue's not-held list has no key for disciplinary findings or tribunals
kind: finding
state: open
use-case: 2 legal counterparty; 6 insurance; 11 healthcare
session: legal-1
opened: 2026-10-21

A template may name only `catalogue.NOT_HELD` keys in a section's
`not_held`. The legal template must say that the Lawyers and Conveyancers
Disciplinary Tribunal's decisions, and the other professional bodies'
disciplinary findings, are not held, and that tribunal decisions (step 5.4
item 5) are not either; `courts` prints "Court judgments" only. The
template states both in its section text and in the flags
`disciplinary-findings` and `court-judgments`, so the memo's not-held line
under the section omits them. For the report lane: add `disciplinary`
("Disciplinary tribunals' findings") and `tribunals` ("Tribunal
decisions"), or widen `courts` to "Court judgments and tribunal decisions".
