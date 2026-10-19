# Three party labels on read returns resolve to no registration
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-20

`keys.parties.party_name(label, rows, on=year)`, given the parties lane's
names, leaves 4 of the 137 party-return rows unresolved, under three
labels, each a filing of a registered party:

- `The Maori Party (Te Pati Maori)`, 2021, two rows: the old and the new
  name together, one in brackets. This is why Te Pāti Māori 2021 does not
  yet equal the frozen site.
- `Animal Justice Party Aotearoa NZ Incorporated`, 2023: `NZ` for New
  Zealand and `Incorporated` after the name.
- `New Zealand Outdoors and Freedom Party`, 2023: `and` for `&` and `New
  Zealand` for `NZ`.

The rows publish with the label as filed and no key. The fix is in
`keys/parties.py` (a bracketed second name tried on its own; `NZ`/`New
Zealand`, `and`/`&` and a trailing `Incorporated` folded before the core
arm), outside the party-returns fence: `bin/fix keys`. The lane replays it
with no change of its own.
