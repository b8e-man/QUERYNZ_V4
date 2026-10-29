# Electorate money waits on the candidate-returns lane
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

The frozen site shows, for every electorate and race, the candidates'
declared donations and expenses from the Commission's candidate-return
summaries and the per-donor lines of the candidates' own returns, and it
gives a donor page to everyone known only from a candidate's return. No
lane publishes candidate returns yet (step 4.1, `candidate-returns`, is
running), so on the rebuilt site every electorate figure, every candidate
figure and the home page's electorate list say "not held", and 1,306 donor
pages known only from candidate returns do not exist. Today: 9,618
differences (electorate 3,532, person pages 3,498, donor 1,476, pickers
623, electorates-by-year 300, home 189).

Which side is right: the frozen one. The rebuilt side is not wrong, it is
not there yet. Clears when the candidate-returns lane publishes and the
template reads it (the site's status names it as next). Owner:
candidate-returns, then site.

Site-2 (2026-10-20): the template reads `pub.candidate_return_totals` and `pub.candidate_return_donors`; 370 of the lane's 380 current returns
join a candidate in the results by year, electorate and surname (7 unjoined: Mana and Rongotai 2020, whose results the house lane does not hold;
3 Tauranga 2022 by-election returns, shown apart on the electorate page); the Commission's figure is the headline with the return's beside it; the
candidate-money gate re-sums the Commission's figures by SQL. Measured against the frozen 2026-10-20T0620, rebuilt in scratch: 9,618 differences
fell to 7,077. What remains is the lane's coverage: the frozen site took the Commission's spreadsheet for every candidate (about 1,139 with figures
across 2017, 2020 and 2023); the lane publishes read returns only (2020: 211, 2022: 3, 2023: 166) and holds no 2017. Still needs: the Commission's
table rows published as rows where no return is read (or the returns read), and 2017 if the window keeps it. Owner: candidate-returns.

Candidate-returns-3 (2026-10-30): the lane publishes the Commission's spreadsheet row where no return is read (675 rows: 2020 363, 2023 312;
`read_from` 'commission', the Commission's figures in the `commission_*` headline columns, the return's own columns NULL, cited by the
spreadsheet's hash, sheet and row). Measured against the frozen 2026-10-29T0616, base and branch built in scratch from the same listing: this
cause 5,133 → 3,189 (electorate 776 → 3, electorates 206 → 2, home 627 → 311, person and party pages 1,570 → 919; donor 1,412 and pickers 542
unchanged); rebuilt-side-wrong 7,216 → 5,280; total 29,186 → 28,619 (cite-key +675, one per new row; nil-return-is-a-zero +740, the
Commission's NIL now $0.00 where the frozen left a blank). What remains: the donor pages, pickers and person pages' donations received wait
on Part A from the scans' readings (ruling 79); the home page's party race totals carry 2017 and the frozen party labels (the window and the
template's label grouping); Christchurch Central 2020 has two Webbs, which the template's surname join rightly refuses. Owner now: site.
For the site: a row with `read_from` 'commission' wants its own citation label (the cite file says "EC candidate return (declaration)") and its
evidence text writes "donations $0.00" from the empty return columns (`render.cites`, `r.get('donations') or 0`); it should state the
Commission's figures, or none.
Site-4 (2026-10-30): the site's part is done. A Commission row's citation file carries its own label ("EC candidate returns
summary (the Commission's spreadsheet row; no return read)") and states the Commission's figures from the `commission_*` columns
(409 of the 675 state a $0.00 the Commission printed, 266 other figures, none read from the empty return columns). Filed party
labels now group the home page's race sections, so this cause on the home page fell 311 → 270 (frozen 2026-10-30T0617, both builds
in scratch); the rest is unchanged: donor 1,412, pickers 542, subject 919, electorate 3, electorates 2. What remains waits on Part A
from the scans' readings (ruling 79), the window (2017) and Christchurch Central 2020's two Webbs. Owner: candidate-returns.
