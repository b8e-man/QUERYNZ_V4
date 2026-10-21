# The catalogue's not-held list has no key for WorkSafe, the regulators, the employment bodies, the Disputes Tribunal or the fire service
kind: finding
state: closed
use-case: 6 insurance underwriting; also 7 construction, 11 healthcare
session: insurance-1
opened: 2026-10-21
closed: 2026-10-21

A template may name only `catalogue.NOT_HELD` keys in a section's
`not_held`, and the memo prints those names under the section. The
insurance template's last section is the safety record, and every register
in it is not held: WorkSafe's prosecutions and enforceable undertakings,
the Commerce Commission's cases, the FMA's warnings and actions, court
judgments, the Employment Relations Authority, the Disputes Tribunal, Fire
and Emergency New Zealand's notices and the companies change history. Only
`courts`, `insolvency`, `securities` and `fsp` exist, so the memo's line
reads "not held: Court judgments, The Insolvency Register, The Personal
Property Securities Register, Financial service providers" under a section
whose text names eleven. The template states the rest in the section's
text and in its blocked flags. For the report lane: add `worksafe`
("WorkSafe prosecutions and enforceable undertakings"), `regulators`
("Commerce Commission and FMA actions"), `employment` ("Employment
Relations Authority determinations"), `disputes` ("Disputes Tribunal
decisions"), `fire` ("Fire and Emergency notices") and `change_history`
("The companies change history before 16 August 2026"). The legal
template's `the-not-held-list-lacks-disciplinary-findings-and-tribunals`
asks the same for tribunals; one change can close both.

Closed 2026-10-21 by the report session (report-3). `catalogue.NOT_HELD`
is now the one list of named registers not held, each with the key a
template cites: `worksafe`, `regulators` ("Commerce Commission and
Financial Markets Authority actions"), `employment`, `disputes`, `fire`,
`tribunals`, `disciplinary`, `company_history` (the key this card called
`change_history`; the construction and credit cards asked for
`company_history`, and one key serves), with `overseas`, `trusts`,
`unincorporated`, `mpi`, `credit_bureau` and `nzbn_interface` from the
other cards; `courts` stays "Court judgments". The memo prints the whole
list with every report, and a section's `not_held` may cite any key. The
insurance template names the eight it needs (a fix in its folder); the
lane for WorkSafe and the regulators is
`worksafe-and-regulator-actions-have-no-lane`, untouched here.
