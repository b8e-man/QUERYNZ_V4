# The property template can now read the Charities Register and the new reaches
kind: finding
state: open
use-case: 12 property developer due diligence
session: fix-report-2
opened: 2026-10-21

The report shape's fix-report-2 (merge request `fix-report-2`, 2026-10-21)
closed the shape's half of the cards this template waited on
(`the-not-held-list-has-no-key-for-the-property-registers`,
`the-officers-reach-does-not-list-an-officers-near-links`,
`the-chain-reach-reads-nothing-on-the-companies-above`). What it lets this
template do, each a fix in `products/templates/12-property/`:

- **The property registers' keys.** `oio`, `building_consents` and `rea`
  are in `catalogue.NOT_HELD`: name them in the not-held section's
  `not_held` so the memo's not-held list and the blanks carry them, and the
  three blocked flags (`overseas-investment`, `building-consents`,
  `real-estate-authority`) point at the keys. The Real Estate Authority key
  says not held until its lane publishes a view.
- **The principals' charities.** The catalogue knows `charities`,
  `charity_officers` (names, suppressed where the row says so; the
  register's `disqualified` mark; roles and dates) and `charity_returns`.
  A developer behind a charitable trust: the two views in `reads` (licence
  "Charities Register open data, Creative Commons Attribution 3.0 New
  Zealand; the register is public under the Charities Act 2005",
  attribution "Charities Services, Department of Internal Affairs") and the
  principals section; a trust board's row in `pub.companies` reaches its
  trustees through the business number (confirmed, `official-number`), and
  a charity officer carrying a principal's name is listed near by name
  (rule `same-name`) until the links lane joins the register
  (`charity-officers-are-in-no-link-and-no-name-row`). The `charities`
  not-held key is out of `catalogue.NOT_HELD` (`SUPERSEDED_NOT_HELD` keeps
  it loadable): every memo now says the template names as not held a
  register that is published and which it does not read; drop it from the
  not-held line and the section's text. Today the walk already meets
  `pub.charities` from the checkpoint's subjects ("views reached but not
  read, because the template does not name them").
- **An officer's near links.** The history, serial, possessions,
  people-notices and Gazette sections name `officers`: a director the links
  lane joins by name alone now lists that row's company, its notices and
  possessions, near with the officer's reason first and the link's own
  after, rule the link's (`near_link` on the item). On GORING DEVELOPMENT
  LIMITED the director's `name-only@1` link lists PJO CONSTRUCTION LIMITED,
  in liquidation, with its notice. `history-reach` can unblock, saying the
  rows are a namesake's until confirmed; `serial-pattern` counts them apart
  from the person's own, amber at most.
- **The companies above.** The chain reads the notices pointing at each
  company above and its current directors, with the company's grade,
  marked `above` at the company's depth, in the `chain` bucket. The chain
  section names `companies` and `shareholders` only and the Gazette section
  does not name `chain`: add `directors` to the chain section's views (or a
  directors-above section naming `chain`) and `chain` to the Gazette
  section's sources; then `holding-chain` need not tell the reader to start
  a report from each company above, and the Gazette section's text drops
  "the Gazette on the companies above in the holding chain is not read".
- **Template parameters.** A template declares the reader's settings in
  `template.toml` (`[[params]]`: name, kind, default, means); the builder
  puts each in `report["params"]` and under its own name on the report.
  `window_days` is read by `rules.py` and not yet declared: card
  `the-construction-and-property-templates-declare-no-window-days-parameter`.

Not a comparison cause. The shape's fixture tests and `python -m
products.report check` hold the reaches; this card is the template's own
reading of them, closed when its sections, flags and tests use them.
