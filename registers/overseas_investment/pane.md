# Overseas investment decisions, on the board

- **Decisions** (`pub.overseas_investment_decisions`, kind decision, key `key`): `case_number` (and every number in
  `case_numbers`), `kind` (Decision or Notification), `outcome` and `section` as stated, `decided_on`,
  `decision_maker`, `pathway` (the kind of consent), `investment_class`; the land as `investment` (street addresses
  and legal descriptions shown as "[street address withheld]" / "[legal description withheld]"; `addresses_withheld`
  counts them), `areas_stated` and `area_ha`; the money under its own heading (`consideration_heading`,
  `consideration_stated`; `consideration_nzd` only for a consideration with one figure and nothing withheld;
  "withheld" where `consideration_withheld`); `penalty_stated`; `rationale` as the office states it; `url` opens the
  office's own summary. A notification is a transaction under a standing consent, not a new decision: `granted` is
  empty.
- **Parties** (`pub.overseas_investment_parties`, under their decision): `role` (applicant, vendor, issuer) and
  `role_stated`, `name` as published ("name withheld" where `withheld`), `status` printed beside it, `trust`,
  `company_number` where printed; ownership as `origins` and `shares`, each as stated (an origin can name a holder),
  `ownership_scope` saying whether the lines are this party's or shared by every party in the cell. `organisation`
  false means "not shown to be an organisation", never "a person".
- **Citation** on every row: the summary's sha256 (`document`), `page`, `place`, `reader`, `profile`,
  `profile_version`; **attribution** "Toitū Te Whenua Land Information New Zealand, CC BY 4.0" beside every row shown.

A summary the office takes down leaves the views at the next load. No street address and no person's home is shown.
