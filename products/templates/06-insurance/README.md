# Template 06: insurance underwriting

Step 5.2, eighth in the plan's order; runs on WorkSafe's releases and the
regulators' actions, with the courts and tribunals waiting, and none of
those is published yet. A subject report (the shape in `products/report/`)
for a commercial underwriter: "what stands against this business and its
people" before pricing the risk.

- `template.toml`: the 12 pub views it reads, each with its licence,
  attribution and refresh; depth 2; its eight sections in the order an
  underwriter reads them (the entity and its namesakes apart; its standing,
  age and registered office; the solvency record in the Gazette, each
  notice dated; its people with their dates; their other companies and how
  each stands; prohibitions and bankruptcies on the people; the people
  beside them and their other roles; the safety record, every register in
  it named as not held); its limits.
- `rules.py`: 23 flags on the bound contract. `sister-company-failure` sets
  each failure of a person's company, dated from its first Gazette
  appointment, beside the person's own role on it; red only where a
  confirmed role began on or before that day and is still listed.
  `officer-churn` counts this year's appointments past the first board and
  never clears. `safety-record` and every not-held register are blocked,
  never clear. From a company the people checks block. `HISTORY = False`.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-21.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check (fast); the real tables through
  `python -m products.report render REF --template insurance` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template insurance` (or a director's ref; add `--html` for the page), or
on the report page (port 8440) choose the template "insurance".
