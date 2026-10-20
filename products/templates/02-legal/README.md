# Template 02: legal counterparty and conflict check

Step 5.2, fourth in the plan's order; runs on held data, with court
judgments (step 5.4) waiting for the full picture. A subject report (the
shape in `products/report/`) for a law firm before it acts: "who is this
counterparty, who stands on its register, and does anyone here already act
for or against them".

- `template.toml`: the 20 pub views it reads, each with its licence,
  attribution and refresh; depth 2 (the conflict web: the people on the
  person's companies, near); six sections in the order a conflicts clerk
  reads them (who the party is and its namesakes apart; officers and
  holders of record with dates; the companies those people share, with
  dates, as the conflict web; the Gazette on the company and its people;
  charity, society and political money; what is not held, court judgments
  and disciplinary findings named); its limits.
- `rules.py`: 27 flags, standing for the old estate's legal checks MC-L1 to
  MC-L5 and its person and company rules where the held registers support
  them, blocked where they do not. The firm's client list is not an input,
  so `client-overlap` is always blocked and no flag says there is no
  conflict. Every rule branches on the start (person, company, other; a
  donation that takes a person's group is that person); from a company the
  people checks block. `HISTORY = False`: the companies file holds current
  roles only, so no check over a person's companies clears. Loaded by path
  by the shape, with `contract` bound; imports nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-21.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check, twelve mutants (fast); the real
  tables through `python -m products.report render REF --template legal`
  (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template legal` (or a director's ref; add `--html` for the page), or on
the report page (port 8440) choose the template "legal".
