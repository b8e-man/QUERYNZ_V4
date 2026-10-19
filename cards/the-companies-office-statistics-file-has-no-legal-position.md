# The Companies Office statistics file has no legal position
kind: finding
state: open
use-case: companies lane, outside check
session: companies
opened: 2026-10-20

`registers/companies/check.py` checks the lane against the Companies
Office's own published counts (quarter-end registered companies, and each
month's incorporations and removals, from
companiesoffice.govt.nz/insights-and-articles/latest-company-statistics/
and its `monthly-company-statistics-since-2001.csv`). No one-page legal
position covers companiesoffice.govt.nz, so the fetch gate refuses it
(hard limit 9), and the figures were read once by the session on 20 October
2026 and pinned in the check. They were confirmed by the old tables
reproducing every month's incorporations to within one.

To close: a legal position for the Companies Office's published
statistics (a government agency's proactive release of aggregate counts;
no personal data), then a small capture of the CSV through the gate, so the
check reads the file by hash instead of pinned figures and stays current
as the Office publishes each month.
