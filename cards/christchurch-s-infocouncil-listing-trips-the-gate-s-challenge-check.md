# Christchurch's InfoCouncil listing trips the gate's challenge check on a page that is not a challenge
kind: finding
state: open
use-case: none (step 6.3, council minutes)
session: councils-1
opened: 2026-10-22

On 22 October 2026 `https://christchurch.infocouncil.biz/` answered 200 with 795,737 bytes carrying 237 minutes
links, and `support.fetchgate.looks_challenged` called it a challenge page: the word `captcha` is in the first 4,096
bytes (a form's script on the page, by the size and the links it carries; not looked at further, because a
challenged read is a failed read and is not retried). The lane holds the instance (`capture_held_hosts`), so
Christchurch's meetings are not in `pub.council_meetings`; 240 of the 1,159 InfoCouncil minutes the old estate kept
as text are Christchurch's.

Fix, for a fix session on `support/fetchgate`: recognise a block by the block page's own landmarks (its title, its
status, its header), as the gate's own docstring and lesson say, and not by a script name on a page that carries
the content asked for. Then a session clears the hold (`DELETE FROM council_minutes.capture_held_hosts WHERE host
= 'christchurch.infocouncil.biz'`, the integrator's hand) and the next nightly run asks again. Until then: a line on
the lane's known limits.
