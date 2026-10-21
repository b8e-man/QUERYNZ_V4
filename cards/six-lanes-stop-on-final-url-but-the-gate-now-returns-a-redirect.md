# Six lanes stop on a redirect by `final_url`; the gate now returns a redirect, so that stop never fires
kind: finding
state: open
use-case: all capture; hard limits 6 and 9
session: fix-support-fetchgate-1
opened: 2026-10-21

From fix-support-fetchgate-1, `fg.open_url` no longer follows a 3xx. It returns the 3xx with
`Fetched.location` (absolute, never fetched) and `final_url` equal to the URL asked. `follow=n` takes up
to n hops, each checked against the positions, recorded and paced.

Six lanes guard "redirected to another host: the run stops" with `fg.host_of(f.final_url) != host`:
`registers/building_practitioners/capture.py:232`, `registers/charities/capture.py:337`,
`registers/courts/capture.py:270`, `registers/real_estate_authority/capture.py:262`,
`registers/tenancy_tribunal/capture.py:271`, `registers/tenders/capture.py:307`.
That guard is now dead: an off-host redirect reaches their `status != 200` branch and is set aside as
"HTTP 302" while the run goes on. Nothing is fetched from the other host, so no limit is broken; the
run is just noisier than designed. A source that redirects on its own host (http to https, a trailing
slash) is now set aside too, where urllib used to follow it silently.

Each lane: stop on `f.location` off its host instead of `f.final_url`; pass `follow=` only where its
source is known to redirect on its own host. Its tests inject a `Fetched` with `final_url` elsewhere, so
they stay green and prove nothing here; add one with `status=302, location=...`.
