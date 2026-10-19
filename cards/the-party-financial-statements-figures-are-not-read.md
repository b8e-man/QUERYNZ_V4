# The party financial statements' figures are not read
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

The lane holds all 46 statements the Commission's roster links (filed
2024 to 2026) and publishes the roster (`pub.party_financial_statements`:
who filed which statement, when, its balance date and audit requirement),
but no figure from inside a statement. The Commission publishes no figure
for them, so there is no outside total to check a reading against; the
check is each statement's own arithmetic (income less expenditure; assets
less liabilities) and the prior-year column of the next year's statement.

The profile exists (`ec-party-financial-statements` v2: layout text where
there is a layer, GLM-OCR for pages without; return only the reported
year's column). The page reader's stored readings cover 33 of the 46 (238
pages, under version 1, at 300 and 200 dots); 13 would need a page-reader
job before they can be replayed. Statements are free-form accounts, not a
form, so a reader needs its headline lines named per statement shape
(income, expenditure, surplus, assets, liabilities, equity) and measured
before anything publishes.

Next: a build session on this lane, tranche "statement figures", text-layer
statements first.
