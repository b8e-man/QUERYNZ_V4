# links — the joining rules, the three tables, the watch, the review agent

See `docs/plan/design.md` "3. Links", `docs/contracts/links.md`, `spec.md` here,
and the module docstring in `__init__.py` for the pieces. Build order:
`links.rows` → `links.old` (once) → `links.build` → `links.pairs` →
`links.measure`; `links.build_all` runs them. `links.check` is the outside check.
