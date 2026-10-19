# A party-year with two returns held is chosen by nobody
kind: finding
state: open
use-case: 1
session: site
opened: 2026-10-20

`pub.party_return_totals` holds two current returns (neither `replaced_by`)
for National 2022 (the party-returns session's queue question to Arthur,
default "neither replaced") and for one unresolved-label party-year in
2023. The frozen site chose one and summed its rows. The template's rule
is that nothing is chosen: the year's declared figure is null with the
basis "2 returns held and none replaced; none chosen", both totals are
listed under `held`, the window total says the year is left out, the
Part A rows of neither are counted on any surface (they are shown on the
donor pages as "shown and not counted"), and the size-bands page skips the
year. The first build counted both returns' Part A rows and overstated
National's named money for 2022 by $2,616,605.90; the fix moved 42 donor
totals down by $5,233,211.80 in all, recorded with `--allow-drop`.

Arthur's ruling on National 2022 (the party-returns queue) resolves it:
once one return is marked replaced, the year comes back on every surface
with no change here. The comparison will card the 2022 difference against
the frozen site until then; this card says which side is right (neither
chose by a ruling; the frozen site chose by code).
