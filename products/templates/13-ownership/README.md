# Template 13: beneficial ownership and anti-money-laundering checks, domestic half

Step 5.2, fifth in the plan's order; ownership chains through held
shareholdings, with sanctions lists, limited partnerships and overseas data
waiting. A subject report (the shape in `products/report/`) for a compliance
team: "who ultimately owns or controls this, and are they exposed".

- `template.toml`: the 22 pub views it reads, each with its licence,
  attribution and refresh; depth 2, the chain two up (`chain_depth = 2`);
  eight sections in the order an analyst reads them (the entity and its
  namesakes apart; its holders of record with their shares and files; the
  holding chain above, two companies up, by name (near) or business number
  (confirmed), with each company's holders, directors and notices; its directors and registered office; the Gazette;
  public office and political money; registered charities (a company's
  by business number, a person's officer rows by name, near); what is not held, sanctions lists,
  limited partnerships, overseas registers, trusts and the securities
  register named); its limits.
- `rules.py`: nineteen flags. The chain names each company holder and
  what was read above it: the companies reached and how, the holders not
  followed, where it was cut (`CHAIN_DEPTH = 4`, the ceiling); the rows
  above are the holder's, never the company's own; for whom shares are held
  and the sanctions check are blocked, never clear; a nominee, trustee or
  custodian is a holder of record and nothing more. Every rule branches on
  the start (company, person, other). Loaded by path by the shape, with
  `contract` bound; imports nothing of it.
- `limits.md`: the known-limits page, the checkpoint of 2026-10-21 and its
  re-renders.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check (fast); the real tables (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template ownership` (add `--html` for the page), or on the report page
(port 8440) choose the template "ownership".
