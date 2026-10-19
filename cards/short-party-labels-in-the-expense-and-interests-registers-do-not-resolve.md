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
