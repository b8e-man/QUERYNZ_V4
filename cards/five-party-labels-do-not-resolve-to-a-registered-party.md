# Five party labels on text-layer returns do not resolve to a registered party
kind: finding
state: closed
closed: 2026-10-20
use-case: 1
session: founding-f05585e
opened: 2026-10-18

`keys.parties.party_name` leaves five labels unresolved on returns the
lane read: `NEW CONSERVATIVE` (2019), `New Zealand Outdoors and Freedom
Party` (2023), `NEW NATION PARTY` (2023), `NewZeal` (2025) and `Heartland
NZ Party` (2021). None is a front-page party; the rows are published with
the label as filed and no registered party, and the page shows them as
unresolved. Two look like spellings of registered names (Outdoors &
Freedom; Conservative Party NZ, if New Conservative is its earlier name),
but the module's own rule is that "New X is not X" is Arthur's judgment,
and a rename is a fact of the Register's lineage, which the parties lane
(step 4) will hold. Not worked here.

## Closed 2026-10-20 (party-returns session 4)

The lane resolves a filed label through `keys.parties.party_name(label,
rows, on=year)` against the parties lane's names (`pub.party_names` with
each registration's window from `pub.parties`; fix-keys-1). Measured over
all 152 landed returns, replay only: of today's 137 rows, the snapshot left
42 rows under 31 distinct labels unresolved; the live path leaves **4 rows
under 3 labels** (114 exact, 8 core, 6 variant, 5 fuzzy). `New
Conservative` resolves to the Conservative Party NZ registration (its
earlier name, in the Register's own lineage), `ONE Party` to NewZeal's.
The row carries the registration's key (`party_key`) and its registered
name (`party`). The frozen-site comparison goes from 71 to 72 equal. The
three labels left are carded for `keys` (`three-party-labels-resolve-to-no-registration`).
