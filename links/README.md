# links — the joining rules, the three tables, the watch, the review agent

See `docs/plan/design.md` "3. Links", `docs/contracts/links.md`, `spec.md` here,
and the module docstring in `__init__.py` for the pieces. Build order:
`links.rows` → `links.build` → `links.old` (the copy of the old ledgers brought level, mapped, promoted) → `links.pairs` →
`links.measure`; `links.build_all` runs them. `links.check` is the outside check.
`links.review` is the review agent (track C): `--score` on the test pairs, `--watched`,
`--job` for the scheduler, `--apply` behind the switch `links.SETTINGS["review_applies"]`.
`links.rows --register <lane>` refills one register's rows alone (rule 10); the links are built whole over the rows.
The rules: two confirm by name (`rules.py`); `seat-and-window@1` and `declared-directorship@1` confirm by a register's own structure;
the rest (`filed-name`, `own-return`, `member-and-party-donor`, `company-name`, `candidate-name-form`, `organisation-name`, `coupled-name`) are near, each with its reason.
Ruling 106: `organisation-sole-company@1` and `candidate-same-party@1` confirm; `successor-name@1` is the one rule of the third grade, `related`
("succeeded by" between two companies, never an identity; `components` walks confirmed links only).
Ruling 107: `organisation-one-live-company@1` confirms a donation row to the one of several companies of its name live in the
donation's year (`rules.one_live_company`, reached through `rules.sole_company`); none or more than one live stays near, the reason saying which.
Ruling 109: `refiled-name@1`, related, "delisted/refiled same year": two companies under one name with no year in brackets, the earlier
removed and the later registered within twelve months of it (either side), a person confirmed on both (`rules.refiled`, `build.refiled_links`).
Ruling 114: the rows read eight more people views (charity officers, Gazette celebrants and practitioners, limited partnership partners,
party board roles, local election candidates, building practitioner decisions, councillor interests); `organisation-sole-company@2` and
`organisation-one-live-company@2` look a donor's organisation name up on the companies, societies, limited partnerships and charities
registers together (`links.bodies`, `rules.sole_body`, `build.body_links`), a body on two registers counted once; @1 is no longer built.
`coupled-name@1` (ruling 73): a donation row filed as two people ("Craig & Shayne Greenlees", `keys.names.is_joint_name`) stays one row and
gains a part row per person (`keys.names.joint_parts`; ref `<donor ref>#<n>`, `part_of` the donor), each joined to the donor, near;
the other rules read a part as any person row. An organisation is never cut on "&"; initials ("M and J Patterson") are not judged.
