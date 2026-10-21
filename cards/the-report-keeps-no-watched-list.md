# The report keeps no watched list, so no subject report is re-run when a register changes
kind: finding
state: open
use-case: 5 business credit and monitoring; also 13
session: credit-1
opened: 2026-10-21

The design says "monitoring is a subject report run again when one of its
registers changes", and use case 5 is "has anything changed for the
companies I am exposed to": a list of entities, not one. The shape saves
memos (`subject_report.reports`) but holds no list of refs to watch and runs
nothing when a monthly file or a Gazette day lands. For the report lane, in
its own state (a product never writes into the estate): a watched list (ref,
template, who added it, when), a re-run when a register the template reads
changes, and the difference against the last saved memo for that ref, as
the change list. The interface check on a schedule for watched entities is
step 5.5's (the companies lane), raised as a request from here. The credit
template needs nothing more than the since-date of
`a-report-takes-no-since-date`, set to the last run.

Read by the report session (report-3) on 2026-10-21 and carded on to step
5.5 (company monitoring, `registers/companies/`, the monitoring design the
plan gives Fable): a watched list needs to know when a register changed,
which only the estate knows (a monthly file landing, a Gazette day, the
interface check), so the trigger is the lane's and the list goes with it.
The shape's part is done: a report takes a since date
(`a-report-takes-no-since-date`, closed) and saved memos are kept in
`subject_report.reports` to diff against. When 5.5 builds the list, the
shape adds the re-run and the difference against the last saved memo for
a ref (raise a card on the report lane then).
