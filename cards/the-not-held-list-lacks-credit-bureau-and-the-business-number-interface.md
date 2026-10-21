# The catalogue's not-held list has no key for credit-bureau data, the business-number interface or the companies change history
kind: finding
state: open
use-case: 5 business credit and monitoring
session: credit-1
opened: 2026-10-21

A section's `not_held` may name only `catalogue.NOT_HELD` keys. Use case 5
must say that credit-bureau defaults and payment records, the
business-number interface's state between monthly files (step 5.5), and the
companies change history before 16 August 2026 are not held; none has a
key, so the memo's not-held list omits them and the credit template names
them in its not-held section's text and in the flags `credit-bureau`,
`interface-freshness` and `change-history`. For the report lane: keys
`credit_bureau` ("Credit-bureau defaults and payment records"),
`nzbn_interface` ("The business-number interface, between monthly files")
and `company_history`, the last one construction-1's
`the-not-held-list-lacks-employment-determinations-and-the-change-history`
also asks for.
