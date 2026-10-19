# Twenty-seven party labels on read returns do not resolve to a registered party
kind: finding
state: open
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
