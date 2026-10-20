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

## 2026-10-20 (parties-2)

`pub.candidates.party` now carries the label as filed, and
`pub.party_labels` holds each with its outcome: on the real tables 49
candidacies are "not a party" (`Independent`, and `IND` on the 2025
by-election list) and 19 carry an unregistered label with "no
registration live then answers to it" (Money Free Party NZ, Te Pāti Hira,
NAP, …). Still needs the site: show the label where the registration is
null.
