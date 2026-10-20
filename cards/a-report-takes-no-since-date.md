# A subject report takes no "since" date, so monitoring cannot say what is new since the last look
kind: finding
state: open
use-case: 5 business credit and monitoring; also 2, 3, 13
session: credit-1
opened: 2026-10-21

Use case 5 is a report re-run on change: a trade credit team asks what
changed for a company since they last looked. The shape builds from a ref
and a template only (`build.build(conn, ref, t)`; the page's `/report/<ref>`
and `?ref=`); there is no date a rule or the memo can read, so the credit
template lists every change it can see, dated by its monthly file, newest
first, and its flag `since-date` is blocked on every report. For the report
lane: a `since` parameter (the page's `?since=YYYY-MM-DD`, the command
line's `--since`) carried in the built report as `report["since"]`, read by
a template's rules through the contract, and printed in the memo's header;
an item dated on or after it marked new. A change dated only to a monthly
file is new when its file's cut is after the date (needs
`the-companies-lane-publishes-no-list-of-its-monthly-files`). The credit
template then splits `monthly-changes` and `recent-adverse-change` into new
and earlier (a fix in its folder).
