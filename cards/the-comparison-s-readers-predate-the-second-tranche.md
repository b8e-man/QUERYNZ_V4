# The comparison's readers predate the second tranche
kind: finding
state: open
use-case: 1
session: site-2
opened: 2026-10-20

Four readers in `checks/comparison_figures.py` were written when the rebuilt side had no electorate money, and now read it wrongly or not at all:
the home page's `electorates` list has no reading on the new side (176 figures: declared and spend per electorate and two totals, all reported as
absent); the year file's money is read from one `money` field where the rebuilt file carries `declared_total` and `expenses_total` per electorate
(142 `expenses_total` aggregates with no part to follow); a person-page candidacy's declared and expenses are hard-coded "not held" on the new side
though the rebuilt page now carries them (one figure today, every joined return once read); a donor's `by_year` on two pages. Together 321 of the
610 uncarded differences of the site-2 rebuild. Nothing on either side is wrong; the readers are behind the shape.

Which side is right: neither; the comparison. Owner: comparison (`checks/` is edited by its own session; the site session ran it and never edited it).
