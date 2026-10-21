# Template 03: banking director history

Step 5.2, third in the plan's order; runs on held data, with the securities
register waiting for the full picture. A subject report (the shape in
`products/report/`) for a bank's credit analyst: "every company this person
has touched, and how each ended".

- `template.toml`: the 22 pub views it reads, each with its licence,
  attribution and refresh; depth 2 (the people beside, near); its seven
  sections in the order an analyst reads them (who the person is and the
  namesakes apart; every directorship and shareholding with its dates; how
  each company ended, its status and Gazette notices dated beneath it;
  prohibitions and bankruptcies on the person; the people they sat beside
  and the companies those people share; society roles, the Charities
  Register (a charity officer row by the person's name, near; a company's
  charity by business number), political money; what is not held, the securities register named); its limits.
- `rules.py`: twenty flags, standing for the old estate's person and company
  rules and its banking checks MC-B1 to MC-B4 where the held registers
  support them, blocked where they do not. Every rule branches on the start
  (person, company, other); from a company the people checks block. The
  companies file holds current roles only, so while `HISTORY = False` no
  check over the person's companies clears. Loaded by path by the shape,
  with `contract` bound; imports nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-20.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check (fast); the real tables through
  `python -m products.report render REF --template banking` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>/director/<id>
--template banking` (or a company's ref; add `--html` for the page), or on
the report page (port 8440) choose the template "banking".
