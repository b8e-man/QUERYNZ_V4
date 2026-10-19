# keys.parties should resolve labels against pub.party_names, by date
kind: blocker
state: open
use-case: 1
session: parties
opened: 2026-10-19

`keys.parties.REGISTERED` is the 18 October snapshot of today's 17
parties, so a return or declaration filed by a deregistered or renamed
party resolves to nothing (cards `twenty-seven-party-labels-on-read-returns-
do-not-resolve`, `five-party-labels-do-not-resolve-to-a-registered-party`).
The parties lane now publishes every registration the documents reach (78) and
every name, abbreviation and printing each carried, with its window
(`pub.party_names`: `party`, `name`, `name_key`, `kind`, `from_on`,
`to_on`). Measured on the published tables with the lane's `name_key`
alone and the filing year inside the registration's window: 31 of the 34
unresolved party-return rows and 46 of the 53 unresolved disclosure rows
find exactly one registration. Left: `Animal Justice Party Aotearoa NZ
Incorporated` (the "Incorporated"), `The Maori Party (Te Pati Maori)`
(the bracketed alias) and `The Greens, Green Party of Aotearoa New
Zealand`, which are the fuzzy arms' work. Proposed for a fix session on
`keys`: `party_name(label, registered=…, on=date)` takes the names and
windows, returns the registration's key with the basis, and keeps every
rule it has (a fuzzy match never joins two parties). `keys/` is outside
the parties session's fence. On node2: `cd /home/user/querynzv4 && bin/fix keys`.
