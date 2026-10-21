# The retirement villages rows in the companies register name no operator and no statutory supervisor
kind: finding
state: open
use-case: 11 healthcare operator governance; also 12
session: healthcare-1
opened: 2026-10-21

`pub.companies` carries 512 rows with `register = 'retirement_village'`
(measured 2026-10-21): the village's name, its registration number, its
status (`REGISTERED`) and its registration day, taken from the old estate's
tables (`source_note`: original not held). No row names the operator, the
statutory supervisor or the day the supervisor changed; no director,
shareholder or office row sits on a village; the only link to a village is
`company-name@1` (164 near links, a village and a company sharing a name).
The old estate measured the same gap (requirements 2.5(a): "NO supervisor
field exists in bulk.retirement_villages (512 rows, operator names only)").
So template 11 names the retirement villages file as not held and blocks
`retirement-villages`, never clear; a report started from a village row
lists no officer and blocks every officer check.

For a lane (plan 5.3, "Retirement villages file: statutory supervisor name
and date; contents need a look"): capture the Registrar of Retirement
Villages' register (the Companies Office publishes it) with each village's
operator (by business number where given) and statutory supervisor, dated,
so a village joins its operator by number, confirmed.
