# A template cannot take the law firm's client list, so the conflict check itself cannot run
kind: finding
state: open
use-case: 2 legal counterparty and conflict check; also 9 (vetting bidders)
session: legal-1
opened: 2026-10-21

The old estate's MC-L4 (`POST /api/entity/{id}/conflicts`) took a firm's
client list, resolved each name against the register (one NZBN, or "name
candidates: n"), and reported each overlap with the web around the
counterparty and its basis. The shape builds a report from one row and a
template; there is no way to hand it a second list, so the legal template's
`client-overlap` flag is always blocked and counts the names a clerk must
compare by hand (19 on CRANELAB's director, 380 on a common name). For the
report lane: let a report take a list of names or refs as an input (never
stored beyond the saved memo, since it is a firm's confidential list), and
expose to templates which listed names meet which rows, by NZBN where the
name resolves to one company and as a name candidate otherwise. The
template then turns `client-overlap` into a fired-or-blocked check (never
clear: absence is not a finding).
