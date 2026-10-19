# The party financial statements' figures are not read
kind: finding
state: closed
use-case: 1
session: party-finance
opened: 2026-10-20
closed: 2026-10-20

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

**Closed, 2026-10-20 (party-finance session 2), text-layer statements.**
`statements.py` reads six headline figures from a statement's text layer
(income, expenditure, surplus; assets, liabilities, net assets) and
publishes a pair only where the statement's own arithmetic holds:
income less expenditure is a surplus line it prints, assets less
liabilities a net-assets line it prints. On all 46 statements: 46 of 92
pairs publish (26 operating, 20 position; 138 figures), every other pair
is a catch-log line, and the prior-year column of each current statement
equals the year before's own figure on 53 of 54 (Green 2025's surplus
line is after tax; 2024's read is before). Shapes met and measured: the
reported year in the later column (Animal Justice 2024), statements in
$000 (Labour 2025 audited, 2026), a dash that is a nil column against one
that is a minus (by where the figure columns end), note numbers, a
scanner's `1 ,953,865`, income and expenditure on facing pages. Two
statements' own arithmetic does not hold and they publish nothing for
that pair: Aotearoa Legalise Cannabis 2024 (its surplus is 21 cents off
its lines) and NZ Loyal 2024 (it brackets a surplus as a loss). The
scanned remainder is card `the-scanned-party-statements-figures-are-not-read`.
