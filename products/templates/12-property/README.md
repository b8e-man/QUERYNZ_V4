# Template 12: property developer due diligence

Step 5.2, tenth in the plan's order. A subject report (the shape in
`products/report/`) for an investor or an apartment buyer: who is really
building this, and what happened to their last projects. Runs on the
companies register's roles, holdings, offices and states and the Gazette's
insolvency notices, mortgagee possessions, prohibitions and bankruptcies;
land titles (LINZ), overseas investment decisions, building consents and
council minutes, the courts, the securities and insolvency registers and
the Real Estate Authority's decisions are named as not held.

- `template.toml`: fourteen published views with their licences, eleven
  sections in the order a buyer reads them, `chain_depth = 2`; from a
  company its directors are followed one step (`officers`), the companies
  at its office listed (`office`) and its company holders followed up
  (`chain`).
- `rules.py`: 23 flags; the serial pattern (MC-P1, the SPV-serial rule) and
  the earlier failure set each dated failure of a principal's companies
  beside a start with the gap in days, the window the reader's
  (`report["window_days"]`, ruling 65; no cut until the shape carries it).
- `limits.md`: what it cannot see, and the checkpoint of 2026-10-21.
- `checkpoint.list`: the twelve subjects.
- `tests/`: fixtures with a mutant check (fast), real tables (slow).

Built by `property-1`.
