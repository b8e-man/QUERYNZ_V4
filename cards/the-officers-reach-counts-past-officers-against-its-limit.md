# The officers reach spends its twelve places on past officers too, so a board with a past officer among its first twelve rows blocks every officer check
kind: finding
state: open
use-case: 11 healthcare operator governance; also 2, 6, 7
session: healthcare-1
opened: 2026-10-21

`walk.follow_officers` (report-3) follows the first `LIMITS["officers"]`
(12) unsuppressed officer rows on an organisation start, in the order the
roles were listed, past officers included. Presbyterian Support New Zealand
Incorporated (`societies:societies/9429043084746`, checkpoint of 2026-10-21)
lists 13 society officers, one of them inactive since 26 March 2024; twelve
were followed and one left, so `officers_omitted` is 1 and template 11's
officer checks (`disqualified-officer`, `officer-bankruptcy`,
`officer-overlap`, `officer-company-notices`) block, never clear, though
every current officer may have been read. For the report lane: follow
current officers first (a director in the latest file with no end filed, a
society officer with no `ended_on`), past officers after, and publish
`officers_omitted_current` beside `officers_omitted` so a template can tell
a current officer left unread from a past one.
