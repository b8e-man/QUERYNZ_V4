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
