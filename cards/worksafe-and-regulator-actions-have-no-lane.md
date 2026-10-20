# WorkSafe's prosecutions and the regulators' actions have no lane, so the insurance template's safety record is always blocked
kind: finding
state: open
use-case: 6 insurance underwriting; also 7 construction, 11 healthcare, 12 property
session: insurance-1
opened: 2026-10-21

Use case 6 runs on "WorkSafe releases, regulator actions" (plan 5.2), and
step 5.3 lists both as held and unread. The insurance template's
`safety-record`, `regulator-actions` and `court-judgments` flags are
therefore blocked on every report, red, and its last section is all
"not held". Measured 2026-10-21 on the old estate (`bin/q --old`): 143
WorkSafe release documents in `registers.worksafe_documents`, read into
`registers.worksafe_enforcement`: 83 prosecutions (decisions 2016-03-23 to
2025-04-15) and 62 enforceable undertakings (accepted 2017-04-05 to
2026-06-29), 76 with a business number; the old requirements (2.7) record
that the official WorkSafe interface gives aggregates only, so the release
texts are the source. The Commerce Commission's 112 cases and the FMA's 16
warnings are parsed with their parties and the Act section empty on all
128 (step 5.3). For a lane session (step 5.3): capture or carry the
release documents, read the prosecution facts (defendant, business number,
offence date, plea, decision, fine, court) and the undertakings at a
"reported" tier with a citation per release, publish a `pub` view the
report's catalogue can name, with the defendant's business number as the
link; then the insurance template reads it and unblocks `safety-record`
(a fix in its folder). The legal position page (hard limit 9) comes with
the lane.
