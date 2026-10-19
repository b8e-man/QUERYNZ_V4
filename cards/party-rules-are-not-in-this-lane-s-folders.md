# Party rules are named in the party-finance spec but held in another folder
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

Step 4.1 lists party rules with party finance, and the lane's first spec
said it owned them. The four folders the brief names (`ec-expenses`,
`ec-financials`, `ec-broadcasting`, `ec-promoters`) hold no party rules:
the old estate keeps constitutions under `var/staging/party-constitutions/`
and the register page links each party's rules (the parties lane reads
that page). The spec now says party rules are not this lane's yet.

Decision for the integrator: take party rules into this lane (a brief
naming `party-constitutions/`, profile `party-constitution` exists) or into
the parties lane, which already reads the links. Recommendation: the
parties lane, since a rule set belongs to a registration and that lane
holds the registrations and their windows.
