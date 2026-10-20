# Template 08: recruitment board screen

Step 5.2, first in the plan's order; runs on held data. A subject report
(the shape in `products/report/`) for a candidate for a board or senior
role: "is there anything in the public record we should know".

- `template.toml`: the 23 pub views it reads, each with its licence,
  attribution and refresh; its seven sections in the order a search
  consultant reads them (who this is and the namesakes apart;
  directorships and holdings of record; Gazette insolvency, bankruptcy and
  prohibition notices; charity and society roles; political money; seats
  and declared interests; what is not held); its limits.
- `rules.py`: thirteen flags, standing for the old estate's seven person
  rules where the held registers support them, and blocked where they do
  not. Loaded by path by the shape; imports nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-20.
- `tests/`: fixtures (fast) and the real tables through
  `python -m products.report render REF --template recruitment` (slow).

Run one: `python -m products.report render companies:<director key>
--template recruitment` (add `--html` for the page), or on the report page
(port 8440) choose the template "recruitment".
