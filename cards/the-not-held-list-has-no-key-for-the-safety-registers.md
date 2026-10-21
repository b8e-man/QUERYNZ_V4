# The catalogue's not-held list has no key for WorkSafe, the regulators, the employment bodies, the Disputes Tribunal or the fire service
kind: finding
state: open
use-case: 6 insurance underwriting; also 7 construction, 11 healthcare
session: insurance-1
opened: 2026-10-21

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
