# Twenty-seven party labels on read returns do not resolve to a registered party
kind: finding
state: closed
closed: 2026-10-20
use-case: 1
session: party-returns
opened: 2026-10-19

Widens `five-party-labels-do-not-resolve-to-a-registered-party` now that
the lane reads the scanned returns: 44 of 99 rows carry a label
`keys.parties.party_name` leaves unresolved, under 27 distinct labels.
Most are small parties that are not front-page parties (ONE Party,
DemocracyNZ, Heartland, Social Credit, NZ Outdoors and Freedom, Animal
Justice, Leighton Baker, Freedoms NZ, Democratic Alliance, New Nation,
Sustainable NZ, TEA, MANA, Advance NZ); some are spellings of registered
names (`The Maori Party (Te Pati Maori)` for Te Pāti Māori 2021, which is
why that party-year does not yet equal the frozen site; `New
Conservative` / `New Conservatives` / `NEW CONSERVATIVE`). Renames are
the Register's lineage, which the parties lane holds; the rows publish
with the label as filed. Not worked here (`keys/` is outside this
session's fence).

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
