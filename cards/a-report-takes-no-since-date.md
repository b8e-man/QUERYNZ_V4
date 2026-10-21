# A subject report takes no "since" date, so monitoring cannot say what is new since the last look
kind: finding
state: closed
use-case: 5 business credit and monitoring; also 2, 3, 13
session: credit-1
opened: 2026-10-21
closed: 2026-10-21

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

Closed 2026-10-21 by the report session (report-3). The shape takes a
since date: `build.build(conn, ref, t, since=…)`, the page's
`?since=YYYY-MM-DD` on `/report/<ref>` and `/report?ref=`, and `render REF
--since YYYY-MM-DD`. The built report carries `report["since"]` (a rule
reads it through the report), every item carries `new` (True when any date
of the row, start, end, on, filed or published, is on or after it; False
when every date is before; None when the row is undated or dated only by a
year or a monthly file, since it cannot say), and the report and each
section count `new` and `cannot_say`. The memo's header says "since …: N
row(s) … marked NEW; M cannot say" and marks each new line. A change
dated only to a monthly file stays "cannot say" until the companies lane
publishes its files' cut dates
(`the-companies-lane-publishes-no-list-of-its-monthly-files`). Measured:
`python -m products.report check` builds the borrower company's report
since the day its possession was entered and since the day after its
publication, and fails unless the notice is new in the first and not in
the second; a fixture test holds the marks and the memo. The credit
template splits `monthly-changes` and `recent-adverse-change` on
`report["since"]` (a fix in its folder).
