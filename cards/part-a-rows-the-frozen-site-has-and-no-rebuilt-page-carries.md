# Part A rows the frozen site has and no rebuilt page carries
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

In a party-year both sides read, a frozen donor page carries a Part A row
that no rebuilt donor page has under any name: "Kelly, Andrew", $25,000 to
National in 2023, is one; eleven donor pages and nineteen picker rows
today. Either the rebuilt reading of that return is short a row, or the
frozen row was a parsing artefact; each needs the return opened at Part A.
The list is in the day record under `<live>/checks/comparison/days/`.

Which side is right: the frozen one until the return says otherwise (its
rows passed the old sum gate). Owner: party-returns.

**Measured (party-returns session 5).** Every published (name, amount)
was set beside the old estate's rows of the same document hash (811 rows
on 42 returns both read). The cause the card guessed at was real once:
ACT 2022 page 2 gave a $50 gift to the next donor and that donor's
$100,000 to "Auckland" (the sum held). Fixed in the layout route; both
rows now match. What is left on returns both read is not a missing row:
Labour 2019 prints one figure per donor where the old estate split it by
date (per-donor totals equal), and two spellings are the page reader's
(`Canivi`/`Caniwi` Capital Partners, NZ First 2019; one NZ First 2025
company). The card's own example, "Kelly, Andrew" $25,000 to National
2023, is on a return set aside for a rounding cent (card
`national-2023-the-rows-add-to-one-cent-more-than-the-printed-total`):
it waits on Arthur's rule. The rest of the day record's list (G M Hyde,
Gloria Bruni, Michael Kelly …) sits on party-years whose rebuilt return
is set aside or whose frozen row came from another copy of the return;
the next comparison run, after the integrator loads this tranche, gives
the count that is left. Stays open.
