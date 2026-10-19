owns: schema `party_finance` (party expense returns, broadcasting allocations, party financial statements, registered promoters and party rules, by document hash) and `party_finance_private` (nothing published lives there)
reads: the Commission's files the old estate already holds under `var/staging/ec-expenses/`, `ec-financials/`, `ec-broadcasting/` and `ec-promoters/`, taken by hash, read-only; fetches nothing until the public site is switched (step 4.1, built; each kind has a document profile)
publishes: `pub.party_expenses`, `pub.party_financial_statements`, `pub.broadcasting_allocations`, `pub.promoters`, each row with its citation
outside check: the Commission's own summary figure for a year and kind (an expense total, an allocation) against the rows for that year
jobs: a `qv4-party-finance-load` job on the scheduler once the lane reads; no capture job before the switch
