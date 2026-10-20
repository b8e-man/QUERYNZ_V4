# The house lane has no result for a race the frozen site shows won
kind: finding
state: closed
use-case: 1
session: comparison
opened: 2026-10-20
closed: 2026-10-20

Mana 2020: the frozen electorate page names the winner (Barbara Edmonds)
and lists eleven candidates; the rebuilt page shows the race with no
result held and no candidates, and the ten frozen person pages whose only
candidacy was Mana 2020 have no rebuilt page. The house lane has not read
that result page (the file is in the listing).

Which side is right: the frozen one. Owner: house.

Closed 2026-10-20 by house-2. The rebuilt race now names its winner. The
winner is the status page's leading candidate, joined to the seat on the
successful-candidates page (Mana: EDMONDS, Barbara; Rongotai: EAGLE, Paul).
`pub.electorates.candidates_held` says the race holds its leading two only.
On a scratch build the four `elected` figures for Mana and Rongotai fall,
and the whole pages under `old-person-no-result` fall from 10 to 9 (Teall
Crossen). Mana's result page itself is not held: the bytes are the old
job's browser error (net::ERR_NAME_NOT_RESOLVED). What is left, the other
candidates, is one cause with
`candidacies-the-frozen-site-shows-and-the-house-lane-lacks`, and the
comparison's rules `house-lane-lacks-a-result` and `old-person-no-result`
should point there.
