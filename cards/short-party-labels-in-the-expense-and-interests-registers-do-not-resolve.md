# Short party labels in the expense and interests registers do not resolve
kind: finding
state: open
use-case: 1
session: interests-expenses
opened: 2026-10-20

`keys.parties.party_name` resolves "Labour", "NZ First" and "Green Party"
but leaves the short labels the two publishers and the interests register
print: "National" (2,599 expense lines, 1,080 returns), "Green" (344;
225), "Act" and "ACT" (352; 88), "Maori"/"Māori" (64; 13), "United Future"
(35; 17), "Progressive" (1; 6), "Mana" (3 returns) and "Independent"
(24; 5, which is not a party). Measured on the full sets in
`scratch_interests_expenses_full`, 20 October 2026: 3,419 of 6,229
expense lines and 1,437 of 2,526 returns carry a label and no registered
party.

The lanes publish the label as printed and NULL for the party, so nothing
is wrong, only unjoined. The fix is in `keys` (a fix session on
`keys/`): the short forms of the registered names, with "Independent"
kept as no party. Historic parties (United Future, Progressive, Mana)
need the parties lane's register lineage.
Blocks: nothing in these lanes; the person links of step 4.2 will want it.

## 2026-10-20 (parties-2): measured through the parties lane's view; ACT still needs keys

Resolved by date against the parties lane's names (`pub.party_labels`,
the full published tables, 20 October): `National`, `Green`, `Maori`,
`United Future`, `Progressive` and `Mana` join their registrations, and
`Independent` is published as not a party. Rows joined, the view against
each lane's own `party`: `pub.mp_expenses` 24,893 of 26,689 (the lane
12,622), `pub.minister_expenses` 12,717 of 13,435 (5,204),
`pub.mp_interest_returns` 2,428 of 2,521 (1,084), `pub.mp_interests`
23,932 of 24,901 (9,483); 0 rows where both join and disagree. Still
needs `bin/fix keys` for `ACT` and `Act`, 3,367 rows across the four
tables: the registered abbreviation is "The ACT Party" and the name key
keeps "actparty" whole. United Future in the quarter from 1 July 2013 (6
rows) rightly joins nothing: the party was off the register from 31 May
to 13 August 2013, and the row says so. The lanes still resolve against
the snapshot: `the-lanes-and-the-site-do-not-yet-join-the-party-labels`.
