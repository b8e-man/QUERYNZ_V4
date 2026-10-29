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

## 2026-10-20 (parties-2)

`pub.candidates.party` now carries the label as filed, and
`pub.party_labels` holds each with its outcome: on the real tables 49
candidacies are "not a party" (`Independent`, and `IND` on the 2025
by-election list) and 19 carry an unregistered label with "no
registration live then answers to it" (Money Free Party NZ, Te Pāti Hira,
NAP, …). Still needs the site: show the label where the registration is
null.

## 2026-10-30 (site-4)

The site shows the label as filed where the official result prints none:
from the return joined to the candidacy (year, electorate, surname, the
money's join) or, where no return is read, the Commission's summary row;
`party_filed_from` says which (`result`, `return`, `commission`) and
`party_filed_basis` says it is the filed label. Of the 135 candidacies
(51 in 2020, 84 in 2023): 34 from a read return, 71 from a Commission
row, 30 blank. Measured against the frozen 2026-10-30T0617, main's code
and site-4's built in scratch from its listing: this cause 106 → 20,
all person pages. What remains: 13 where the Commission's row itself
leaves the party cell blank and the frozen site wrote "Independent" (the
template does not infer a label from a blank; whether a blank cell means
Independent is the candidate-returns lane's to read off the spreadsheet,
not the site's to guess); 7 with no return and no Commission row joined
(a "Return not received" row is not published, or no row). Owner now:
candidate-returns, for the blank cells.
