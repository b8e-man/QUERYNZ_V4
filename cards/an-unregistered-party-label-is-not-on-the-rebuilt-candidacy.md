# An unregistered party label is not on the rebuilt candidacy
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

The frozen person page shows a candidacy's party as filed: "Independent",
or an unregistered label such as "Future Youth Party". The rebuilt
candidacy names the registered party and shows nothing for the rest (both
`party` and `party_filed` are null). Today: 106 candidacies.

Which side is right: the frozen one; the label is in the result. Owner:
house (publish the label as filed), then site.

House, 20 October (house-2). The frozen side is right, but no file this
lane reads carries the label. Where a candidate's party has no list, the
official result prints an empty party cell beside the candidate: 51
candidacies in 2020 and 84 in 2023, and none of them is among the status
page's two leaders. The 2020 and 2023 nomination lists are not held (card
`the-2020-and-2023-party-lists-are-not-held`). The label as filed is on the
candidate's return, which is the candidate-returns lane's document:
`pub.candidate_return_totals.party` carries it for the 382 returns that lane
reads with a party (18 "Independent" and 5 "Vision New Zealand" among them).
The frozen site took the label from the Commission's summary spreadsheet,
which covers every candidate who filed. house-2 makes `party_basis` on those
rows say so.

Still needs: the site to show the filed label from the candidate return
wherever the result prints none, joined the way candidate-returns already
joins (year, electorate, surname); and candidate-returns to publish the
summary's party for the returns it has not read. Owner from here: site, with
candidate-returns.
