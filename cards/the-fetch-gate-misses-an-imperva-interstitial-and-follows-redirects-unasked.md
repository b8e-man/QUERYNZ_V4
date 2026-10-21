# The fetch gate misses Imperva's interstitial, and follows a redirect to a host it never judged
kind: finding
state: closed
use-case: all capture; hard limits 6 and 9
session: grants-1
opened: 2026-10-21
closed: 2026-10-22

Two gaps in `support/fetchgate`, met by grants-1 on 21 October 2026. Owner: a fix session on `support/fetchgate`.

1. `catalogue.data.govt.nz/dataset?q=…` answered HTTP 200 with Imperva's interstitial: title "Pardon Our
   Interruption", a `reeseSkipExpirationCheck` script, `X-SPA-INTERSTITIAL`. `looks_challenged` returned "" (none of
   `CHALLENGE_MARKS` is in it), so `Fetched.blocked` was empty and the page was landed in the sample database's store
   as a document (`fe3dcaa5…`, held, never read). Tenders-1 met the same wall on `www.data.govt.nz` and called it
   Incapsula. Add "pardon our interruption" and "reese84" to `CHALLENGE_MARKS`. `registers/grants/capture.py`
   carries them meanwhile (`MORE_CHALLENGE_MARKS`), with a test on the real page.
2. `open_url` lets urllib follow redirects, so the gate's position check covers the first host only. The survey's
   request to `https://www.trillian.nz` was answered from `www.trillian.co.nz`, a host no position on file named at
   that moment; the next request, to that host directly, was refused. A redirect should be returned, not followed,
   and the caller asks the gate about the new address. `registers/grants/capture.py` does this itself
   (`fetch_once`, `get_following`) through `open_url`-free requests that still take the gate's decision and pace.

Closed at the merge of `fix-support-fetchgate-1` (22 October 2026): Imperva's interstitial (its title, its header, the reese84 script) is a blocked read; `open_url` returns a redirect to another host unfetched, with `follow=` for a caller that wants each hop judged; the integrator added a same-host default (up to three hops on the host asked) so within-host redirects keep reading. The lane's own `MORE_CHALLENGE_MARKS` and redirect handling may now be dropped (a note for the grants lane).
