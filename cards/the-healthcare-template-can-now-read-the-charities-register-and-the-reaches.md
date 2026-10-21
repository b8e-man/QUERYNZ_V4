# The healthcare template can now read the Charities Register and the new reaches
kind: finding
state: closed
use-case: 11 healthcare operator governance
session: fix-report-2
opened: 2026-10-21
closed: 2026-10-22

The report shape's fix-report-2 (merge request `fix-report-2`, 2026-10-21)
closed the shape's half of the cards this template waited on
(`the-report-cannot-reach-the-charities-register`,
`the-not-held-list-has-no-key-for-the-health-registers`,
`the-officers-reach-does-not-list-an-officers-near-links`,
`the-chain-reach-reads-nothing-on-the-companies-above`). What it lets this
template do, each a fix in `products/templates/11-healthcare/`:

- **The Charities Register.** The catalogue knows `charities`, `charity_officers`
  (names, suppressed where the row says so; the register's `disqualified`
  mark in the statement; `role`, `status`, `started_on`, `ended_on`; a
  withheld name field as the row's note) and `charity_returns` (dated
  "period to", newest first, the figures as filed). Name them in `reads`
  (licence "Charities Register open data, Creative Commons Attribution 3.0
  New Zealand; the register is public under the Charities Act 2005",
  attribution "Charities Services, Department of Internal Affairs"):
  `charities` and `charity_officers` in the governance section,
  `charity_returns` in the charity-returns section (`views = []` today). The
  five charity flags (`charity-arm`, `charity-returns`,
  `charity-audit-opinion`, `charity-return-filed`, the charity half of
  `disqualified-officer`) already read the views by name and unblock the day
  `reads` names them. The reaches: a company's charity by its business
  number (an entity of the walk, confirmed, rule `official-number`), so an
  operator's charitable trust board (Ryman Healthcare Charitable Trust,
  Presbyterian Support (Northern)) reaches its trustees and the officer
  checks that blocked on "0 officers" can read them, graded as the charity
  row is; the charity's officers and returns beneath it; and a charity
  officer that carries a person's name listed near by name with the reason
  "no link joins the Charities Register's officers to any other row yet"
  (rule `same-name`; the links lane's join is carded in
  `charity-officers-are-in-no-link-and-no-name-row`). A rule over by-name
  officer rows is amber at most until then.
- **The `charities` not-held key.** It is out of `catalogue.NOT_HELD`
  (`SUPERSEDED_NOT_HELD` keeps it loadable). Every memo of this template now
  says under "what the walk left out" that it names as not held a register
  that is published and which it does not read. Drop `charities` from the
  two `not_held` lines and from the two sections' text;
  `tests/test_healthcare_real.py` (line 70) asserts "not held: Charities
  register and officers" and changes with it.
- **The health registers' keys.** `retirement_villages`, `hdc`,
  `certification`, `health_providers` and `aged_care_commissioner` are in
  `catalogue.NOT_HELD`: name them in the not-held section's `not_held` (and
  `retirement_villages` on the standing section) so the memo's not-held list
  and the blanks carry them, and the five blocked flags point at the keys.
- **An officer's near links.** The overlap and Gazette sections name
  `officers`: a director the links lane joins to another director row by
  name alone now lists that row's company and its notices, near with the
  officer's reason first and the link's own after, rule the link's
  (`near_link` on the item). The overlap and notices-on-other-companies
  checks can count them as near, never as the person's own.
- **The companies above.** The governance section names `chain` with
  `directors` among its views, so the current directors of a company above
  in the holding chain are listed there now, marked `above` at their depth
  (the memo says "on a company N up the chain"); the Gazette section does
  not name `chain`, so the notices on a company above are walked and not
  listed until it does.
- **Template parameters.** A template declares the reader's settings in
  `template.toml` (`[[params]]`: name, kind, default, means); the builder
  puts each in `report["params"]` and under its own name on the report.
  This template declares none and reads none.

Not a comparison cause. The shape's fixture tests and `python -m
products.report check` hold the reaches; this card is the template's own
reading of them, closed when its sections, flags and tests use them.

Progress, fix-templates-1 (2026-10-21): the Charities Register bullet and the
`charities` not-held key are done: the three views in `reads`; `charities`
and `charity_officers` in the governance section (`named` added), the returns
in the charity-returns section, `charity_officers` in the overlap section;
`charities` out of both `not_held` lines; the charity flags read the views; a
trust board's trustees are read from its own charity for the disqualified mark
(red with no end filed), not followed; a by-name row is amber at most. Fixture
test `test_the_charities_register_is_read_by_number_and_by_name`, three new
mutants; checkpoint re-rendered (limits.md). Still open, outside that brief:
the health registers' not-held keys, an officer's near links, and the
companies above (`chain` in the Gazette section).

Closed by fix-products-templates-1 (2026-10-22): the five health keys in the
not-held section's `not_held` (`retirement_villages` on the standing section
too), and the five blocked flags naming each register as the catalogue's key
does; an officer's near links counted apart in `officer-overlap` and
`officer-company-notices` (info alone, never amber, never a clear while one
stands; a prohibition or bankruptcy reached by one never red); `chain` in the
Gazette section, a notice on a company above set beside the entity's own in
`insolvency-notice` and never counted as an officer's company's. Fixture test
`test_the_reaches_name_the_health_keys_an_officers_near_links_and_the_companies_above`
and five new mutants; the checkpoint re-rendered (limits.md).
