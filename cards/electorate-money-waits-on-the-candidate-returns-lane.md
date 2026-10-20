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
