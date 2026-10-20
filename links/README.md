# links — the joining rules, the three tables, the watch, the review agent

See `docs/plan/design.md` "3. Links", `docs/contracts/links.md`, `spec.md` here,
and the module docstring in `__init__.py` for the pieces. Build order:
`links.rows` → `links.build` → `links.old` (the copy of the old ledgers brought level, mapped, promoted) → `links.pairs` →
`links.measure`; `links.build_all` runs them. `links.check` is the outside check.
`links.review` is the review agent (track C): `--score` on the test pairs, `--watched`,
`--job` for the scheduler, `--apply` behind the switch `links.SETTINGS["review_applies"]`.
`links.rows --register <lane>` refills one register's rows alone (rule 10); the links are built whole over the rows.
The rules: two confirm by name (`rules.py`); `seat-and-window@1` and `declared-directorship@1` confirm by a register's own structure;
the rest (`filed-name`, `own-return`, `member-and-party-donor`, `company-name`, `candidate-name-form`, `organisation-name`) are near, each with its reason.
