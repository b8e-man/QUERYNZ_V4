# The insurance template can now read the Charities Register
kind: finding
state: closed
use-case: 6 insurance underwriting
session: fix-report-2
opened: 2026-10-21
closed: 2026-10-21

The report shape's fix-report-2 (merge request `fix-report-2`, 2026-10-21)
closed the shape's half of the cards this template waited on. What it lets
this template do, each a fix in `products/templates/06-insurance/`:

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
  `not_held` line: this template names none, so nothing to drop; an insured's charitable arm is readable if a section wants it.
- **Template parameters.** A template declares the reader's settings in
  `template.toml` (`[[params]]`: name, kind, default, means); the builder
  puts each in `report["params"]` and under its own name on the report.
  This template declares none and reads none.

Not a comparison cause. The shape's fixture tests and `python -m
products.report check` hold the reaches; this card is the template's own
reading of them, closed when its sections, flags and tests use them.

Closed by fix-templates-1 (2026-10-21): the three views in `reads` and a new charities section after the people beside (sources `named`, `roles`, `members`, `confirmed`): a company's charity by business number with its officers and returns, a person's officer rows by name, near. The template named no `charities` not-held key and declares no charity flag, so none changed. Fixture test `test_it_reads_the_charities_register_in_a_section_of_its_own`; the checkpoint re-rendered (limits.md).
