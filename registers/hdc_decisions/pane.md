# Health and Disability Commissioner decisions, on the board

- **Decisions** (`pub.hdc_decisions`, kind decision, key `key`): `case_number` and `decided_on`, `kind` (the gravest
  finding the page states: breach, adverse comment, educational comment, other comment, no breach; or 'case study'),
  `findings` per party ("Waikato District Health Board — breach", "Registrar — adverse comment"), `provider_kinds`,
  `occupations` and `rights_tagged` as the Commissioner classifies the page, `rights_breached` as stated,
  `recommendation_headings` and `recommended_to`, `named_roles` with `naming_grounds` beside each; `url` opens the
  Commissioner's own page (empty for a case study, whose address is its summary). A finding is the Commissioner's
  opinion under the Code of Rights, not a court's: the pane says so beside every row.
- **Providers** (`pub.hdc_decision_providers`, under their decision): `name` as the Commissioner names it, with
  `abbreviation` and `also_called`, its `findings` and `rights_breached`, `recommended`, and `company_number` or
  `charity_number` only where the page prints one beside the name. A provider the Commissioner does not name is never
  a row; it shows on the decision as "an unnamed <kind>".
- **Citation** on every row: the page's sha256 (`document`), `page`, `place`, `reader`, `profile`, `profile_version`.

No heading, consumer, family member, letter label, age, condition, place beyond the provider, or practitioner's name.
Held until the Commissioner's written permission is on file: the views are empty until then.
