# The banking template can now read the Charities Register
kind: finding
state: closed
use-case: 3 banking director history
session: fix-report-2
opened: 2026-10-21
closed: 2026-10-21

The report shape's fix-report-2 (merge request `fix-report-2`, 2026-10-21)
closed the shape's half of the cards this template waited on. What it lets
this template do, each a fix in `products/templates/03-banking/`:

- **The Charities Register.** The catalogue knows `charities`, `charity_officers`
  (names, suppressed where the row says so; the register's `disqualified`
  mark in the statement; `role`, `status`, `started_on`, `ended_on`; a
  withheld name field as the row's note) and `charity_returns` (dated
  "period to", newest first, the figures as filed). Name them in `reads`
  (licence "Charities Register open data, Creative Commons Attribution 3.0
  New Zealand; the register is public under the Charities Act 2005",
  attribution "Charities Services, Department of Internal Affairs") and in
  the sections that want them. The reaches: a company's charity by its
  business number (an entity of the walk, confirmed, rule `official-number`),
  the charity's officers and returns beneath it, and a charity officer that
  carries a person's name listed near by name with the reason "no link joins
  the Charities Register's officers to any other row yet" (rule `same-name`;
  the links lane's join is carded in `charity-officers-are-in-no-link-and-no-name-row`).
  Until the links lane joins the register, a rule over by-name officer rows
  is amber at most, never red on its own.
- **The `charities` not-held key.** It is out of `catalogue.NOT_HELD`
  (`SUPERSEDED_NOT_HELD` keeps it loadable). Every memo of this template now
  says under "what the walk left out" that it names as not held a register
  that is published and which it does not read. Drop `charities` from each
  `not_held` line (two here) and from the not-held section's text.
- **The two charity flags.** `charity-officer-roles` and `charity-integrity-marks`
  are blocked on `CHARITIES_NOT_HELD`. Rewrite them to read `charity_officers`
  rows: the person's charity roles with their dates (near where matched by
  name, confirmed where reached through the person's own company's charity),
  and the `disqualified` mark and the officer's `status`; `CHARITIES_NOT_HELD`
  comes out. Any test asserting "not held: Charities register and officers"
  in a memo changes with it.
- **Template parameters.** A template declares the reader's settings in
  `template.toml` (`[[params]]`: name, kind, default, means); the builder
  puts each in `report["params"]` and under its own name on the report.
  This template declares none and reads none.

Not a comparison cause. The shape's fixture tests and `python -m
products.report check` hold the reaches; this card is the template's own
reading of them, closed when its sections, flags and tests use them.

Closed by fix-templates-1 (2026-10-21): the three views in `reads` and the money section (sources `named` and `roles`); `charities` out of both `not_held` lines and the texts; `charity-officer-roles` lists the charity officer rows carrying the person's name (near) and, from a company, its charity by business number; `charity-integrity-marks` reads the register's `disqualified` mark, red on a confirmed row of the company's own charity, amber by name, clear only where the name was looked up, the view not skipped and nothing left past the limit; `CHARITIES_NOT_HELD` out. Fixture test `test_the_charity_flags_read_the_register_by_name_and_by_number` and two mutants; the checkpoint re-rendered (limits.md).
