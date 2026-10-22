# Christchurch's InfoCouncil listing trips the gate's challenge check on a page that is not a challenge
kind: finding
state: closed
use-case: none (step 6.3, council minutes)
session: councils-1
opened: 2026-10-22
closed: 2026-10-23

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

Closed 2026-10-23 by the fix session fix-support-fetchgate-1. `looks_challenged`
now recognises a block by the block page's own landmarks: its status, its own
header, or its title (searched in the first 64 KiB, so a title after a large
inline style is found). A mark such as `captcha` near the top counts only on
a body no bigger than a challenge page, `CHALLENGE_PAGE_MAX` = 64 KiB
(Cloudflare's shell is 29,045 bytes). A bigger page carries the content
asked for, and a word or a script name in it no longer makes it a challenge.
Test: a fixture built from the listing's shape (795,737 bytes, 237 minutes
links, `captcha` in a form's script in the first 4,096 bytes) is not a
challenge, directly and through `open_url`; the old gate calls it one. The
Cloudflare challenge and block pages and the Incapsula, Imperva and Radware
shapes are still failed reads, and so is a 900 KB page titled "Just a
moment...". The hold is NOT cleared here: after the merge the integrator
deletes Christchurch's row from `council_minutes.capture_held_hosts` and the
next nightly run asks again.
