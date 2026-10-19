# The frozen site shows no large-donation declaration from 2019 to 2022
kind: finding
state: open
use-case: 1
session: disclosures
opened: 2026-10-19

The frozen site's large donations (`home.json`, `disclosed_by_year`) hold
2023 and 2026 only. The Commission's own table lists declarations for the
whole 2019 window: under the over-$30,000 regime, 8 received by the
Commission in 2019, 27 in 2020, 13 in 2021 and 47 in 2022 (counted by the
Commission's date, not yet by the day the party received the gift). The old
feed read only the over-$20,000 page and never its `donations-exceeding-30000`
sub-page, which the old job did capture.

The disclosures lane holds them all (`pub.disclosures`, regimes
`over-30000-2011-2022` and `over-20000-2008-2010`, 244 declarations). A
declaration of that regime is one donor's gifts that together passed
$30,000, itemised as free text, so it is a different unit from the 2023
rows: the Follow the Money template decides how to show it, and that the
threshold changed. Reproduce the frozen site first (step 4.5); this is a
hole on record, not a silent fix.
