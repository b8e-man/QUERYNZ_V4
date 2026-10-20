# A renamed party's public money is summed under one name
kind: finding
state: closed
closed: 2026-10-20
use-case: 1
session: comparison
opened: 2026-10-20

The parties lane treats a renamed party as one party (the plan's rule for
the register), so a party's broadcasting allocation and expenses across
both names sum under the current name: Conservative Party NZ carries
$204,059 allocated (2020 under its old name and 2023 as New Conservative)
where the frozen site shows $64,609; NZ Outdoors & Freedom Party carries
2020's $53,840 where the frozen site, which did not join the names, shows
nothing. Today: 34 figures on the home page and the party pages.

Which side is right: the rebuilt one, if the lane's rename table is right
that these are one party; the table is the authority and the lane should
confirm these two. Owner: parties.

## Closed 2026-10-20 (parties-2): confirmed, the rebuilt side is right

Both are renames the Commission states in its Gazette notices, now read
from the Gazette lane's copy (`pub.party_events`, `gazette_key`):
Conservative Party of New Zealand → New Conservative on 8 August 2018
(2018-au3933), → New Conservatives on 6 September 2023 (2023-au4224), →
Conservative Party NZ on 28 January 2026 (2026-au363), one registration
`ec-party/2011-10-06/b6d48b3f9ebc`; NZ Outdoors Party → NZ Outdoors &
Freedom Party on 6 April 2022 (2022-au1366), one registration
`ec-party/2017-08-11/dd6cf11df885`. The register page prints each under
its new name with the old registration's day (the window check, green).
`pub.party_labels` joins `New Conservative` 2020 and 2023 and `NZ
Outdoors Party` 2020 in `pub.broadcasting_allocations` to those
registrations, as the party-finance lane does (0 rows disagreeing). The
rebuilt $204,059 is 2020's varied allocation ($64,609, as New
Conservative) plus 2023's last ($139,450): the one party's. Nothing
changes; the comparison's rule keeps this card as the cause.
