# The comparison's readers predate the second tranche
kind: finding
state: closed
use-case: 1
session: site-2
opened: 2026-10-20
closed: 2026-10-20

Four readers in `checks/comparison_figures.py` were written when the rebuilt side had no electorate money, and now read it wrongly or not at all:
the home page's `electorates` list has no reading on the new side (176 figures: declared and spend per electorate and two totals, all reported as
absent); the year file's money is read from one `money` field where the rebuilt file carries `declared_total` and `expenses_total` per electorate
(142 `expenses_total` aggregates with no part to follow); a person-page candidacy's declared and expenses are hard-coded "not held" on the new side
though the rebuilt page now carries them (one figure today, every joined return once read); a donor's `by_year` on two pages. Together 321 of the
610 uncarded differences of the site-2 rebuild. Nothing on either side is wrong; the readers are behind the shape.

Which side is right: neither; the comparison. Owner: comparison (`checks/` is edited by its own session; the site session ran it and never edited it).

Closed 2026-10-20 by comparison-2. The readers read the template's second
version on both sides: the home page's electorates (window total and each
year per electorate), the year files' own figures (declared total,
candidates, winner per electorate; the all-years file's window totals
only), the person page's candidacy money, and a party name listed twice
on the rebuilt home (the entry with most to show stands). The fourth item,
a donor's by-year on two pages, was the frozen site keying a care-of
("C/- …") as a second donor; the rows rule now names it `fold-differs`.
Every section the template's `page_sections` lists is read as figures on
both sides too (the home page's eleven money sections, the parties page's
three, the party page's statements, members, made, sighted, top ten,
leaders and rules; the person page's received, positions, properties,
boards, expenses and the interests tree; the electorate page's window
money), and `sections_added` is read so the shape's own keys are not
counted. Measured on frozen 2026-10-20T0620 against rebuilt
2026-10-20T1513: 614 uncarded fell to 0; 30,497 differences became 29,508
with 1,500 more figures read per home page.
