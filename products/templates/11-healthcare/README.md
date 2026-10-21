# Template 11: healthcare operator governance

Step 5.2, ninth in the plan's order; runs on the retirement villages file
and the charity returns, with the Health and Disability Commissioner's
decisions waiting. A subject report (the shape in `products/report/`, its
third tranche `report-3`: it loads only on that shape) for an aged-care
investor or a regulator's analyst: who governs this operator, what its
charity arm files, and where its officers overlap.

- `template.toml`: the 13 pub views it reads, each with its licence,
  attribution and refresh; depth 2, the chain two up; seven sections in the
  order an investor reads them (the entity and its namesakes apart; its
  standing and age; its governance: directors, holders of record, the
  chain, and the charities its people serve; the charity's annual returns;
  officer overlap, through the `officers` reach; the Gazette on the entity,
  its people and its people's companies; what is not held); its limits.
  The Charities Register's three views are read: a company's charity by
  business number (confirmed), a person's officer rows by name (near).
- `rules.py`: 21 flags on the bound contract. `officer-overlap` sets each
  officer's other current roles beside the officer's role on the entity,
  dated, care-named organisations counted apart and the entity's own name
  word apart again, hubs never amber. `disqualified-officer` and
  `officer-bankruptcy` read the Gazette on each officer's record (and the
  Charities Register's disqualified mark: red on the entity's own charity's
  officers, amber on a row matched by name). `charity-arm`,
  `charity-returns`, `charity-audit-opinion`, `charity-return-filed` read
  the charity views.
  `retirement-villages`, `hdc-decisions`, `certification-audits`,
  `provider-registers`, `aged-care-commissioner`, `court-judgments`,
  `past-roles` are blocked, never clear. A start that lists no officer
  blocks every officer check.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-21.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check of eighteen breaks (fast); the real
  tables through `python -m products.report render REF --template
  healthcare` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template healthcare` (or a society's or a director's ref; add `--html`
for the page), or on the report page (port 8440) choose the template
"healthcare".
