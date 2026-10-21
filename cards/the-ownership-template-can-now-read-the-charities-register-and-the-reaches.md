# The ownership template can now read the Charities Register and the companies above
kind: finding
state: open
use-case: 13 beneficial ownership and AML checks, domestic half
session: fix-report-2
opened: 2026-10-21

The report shape's fix-report-2 (merge request `fix-report-2`, 2026-10-21)
closed the shape's cards on the charities views and the chain. What it lets
this template do, each a fix in `products/templates/13-ownership/`:

- **The companies above.** This template sets no `chain_depth` and names
  no `chain` bucket. With `chain_depth = 2` and a section naming `chain`
  with `companies`, `shareholders`, `directors` and the Gazette views, the
  holding chain above a company is listed with each company's current
  directors and the notices on it, by business number confirmed and by a
  unique name near, each holder's shares as filed, never as a fraction, a
  cut chain saying it goes on, and the memo counting what was read on the
  companies above: the domestic half's chain of record.
- **A charity in the chain.** The catalogue knows `charities`,
  `charity_officers` and `charity_returns` (licence "Charities Register
  open data, Creative Commons Attribution 3.0 New Zealand; the register is
  public under the Charities Act 2005", attribution "Charities Services,
  Department of Internal Affairs"). A charitable trust holding shares of
  record reaches its charity row by business number (confirmed,
  `official-number`) and its trustees beneath it; a charity officer carrying
  a person's name is listed near by name until the links lane joins the
  register (`charity-officers-are-in-no-link-and-no-name-row`). The
  `charities` not-held key is out of `catalogue.NOT_HELD`
  (`SUPERSEDED_NOT_HELD` keeps it loadable): every memo now says the
  template names as not held a register that is published and which it
  does not read; drop it from the not-held line and the section's text.
- **Template parameters.** A template declares the reader's settings in
  `template.toml` (`[[params]]`: name, kind, default, means); the builder
  puts each in `report["params"]` and under its own name on the report.
  This template declares none and reads none.

Not a comparison cause. The shape's fixture tests and `python -m
products.report check` hold the reaches; this card is the template's own
reading of them, closed when its sections, flags and tests use them.

Progress, fix-templates-1 (2026-10-21): the Charities Register half is done:
the three views in `reads` and a new charities section before what is not
held (sources `named`, `roles`, `members`, `confirmed`); `charities` out of
the not-held line and its text. Fixture test
`test_it_reads_the_charities_register_in_a_section_of_its_own`; checkpoint
re-rendered (limits.md). Still open, outside that brief: the companies above
(`chain_depth = 2`, a section naming `chain`), which is also what would reach
a charitable trust holding shares of record.
