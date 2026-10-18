# The fetch gate's floor table should carry the two windowed hosts at five seconds
kind: finding
state: open
use-case: -
session: windowed
opened: 2026-10-18

Both positions (`docs/legal/positions/tenancy-tribunal-decisions.md`,
`real-estate-authority-decisions.md`) set a floor of 5 s. `support/fetchgate`
is outside the windowed fence, so the lanes hold the floor themselves
(`FLOOR_S = 5.0`, a lane-side pacer before every gated request); the gate's
own floor for `decisions.dotnous.com` is its default 1.5 s, and for
`forms.justice.govt.nz` 5 s only because that host resets the connection on
`robots.txt` (the polite floor for an unreadable robots file). The one home
for a stated floor is `FLOORS` in the gate. Fix: add
`"forms.justice.govt.nz": 5.0` and `"decisions.dotnous.com": 5.0` to
`support.fetchgate.FLOORS`, so the floor holds for any caller, not only these
lanes.
