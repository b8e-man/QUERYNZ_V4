# Template 05: business credit and monitoring

Step 5.2, seventh in the plan's order; runs on the monthly grain of the
companies files and the Gazette, with step 5.5 (the business-number
interface), the Insolvency Register and the securities register waiting. A
subject report (the shape in `products/report/`) for a trade credit team:
"has anything changed for the companies I am exposed to, and what stands
against this one today", re-run on change.

- `template.toml`: the 12 pub views it reads, each with its licence,
  attribution and refresh; depth 2; seven sections in a credit analyst's
  order (the entity and its namesakes apart; its standing today; what
  changed, each director, holder and registered office with the monthly
  files that show it; the Gazette on the entity; its people; prohibitions
  and bankruptcies among them; what is not held, each named); its limits.
- `rules.py`: twenty-five flags on the bound contract. `monthly-changes`
  lists every change between the files, newest first, dated by its file with
  the grain stated; `recent-adverse-change`, `officer-churn`,
  `insolvency-notices`, `register-events`, `young-entity`,
  `people-failed-companies` and the rest; every rule branches on the start
  (company, person, other); from a company the people checks block. While
  `STATES = False` (status and name changes unreachable) no change check
  clears; while `HISTORY = False` no check over a person's companies clears.
  Loaded by path by the shape, with `contract` bound; imports nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-21.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check (fast); the real tables through
  `python -m products.report render REF --template credit` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template credit` (or a director's ref; add `--html` for the page), or on
the report page (port 8440) choose the template "credit".
