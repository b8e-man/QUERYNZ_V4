# Template 04: agriculture counterparty

Step 5.2, second in the plan's order; runs on held data. A subject report
(the shape in `products/report/`) for an agribusiness credit manager, or a
farm business owner and their accountant: "what does the record say about
this trading company and the people behind it".

- `template.toml`: the 22 pub views it reads, each with its licence,
  attribution and refresh; its seven sections in the order a credit
  decision reads them (who the counterparty is and its namesakes apart;
  its officers and holders of record with dates; Gazette receiverships,
  liquidations, winding-up applications, administrations, creditors'
  notices and removals, bankruptcies and prohibitions; the people's other
  companies and what became of them; society roles and the Charities
  Register (an officer row by the counterparty's name, near; a company's
  charity by business number); political
  money; what is not held); its limits.
- `rules.py`: nineteen flags, standing for the old estate's four company
  rules (group-receivership, practitioner-repeat, partnership-dissolved,
  mpi-coverage) where the held registers support them, and blocked where
  they do not. Loaded by path by the shape; imports nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-20.
- `checkpoint.list`: six subjects as register keys (since 2026-10-21).
- `tests/`: fixtures (fast) and the real tables through
  `python -m products.report render REF --template agriculture` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template agriculture` (or a director's ref; add `--html` for the page),
or on the report page (port 8440) choose the template "agriculture".
