# Six lanes stop on a redirect by `final_url`; the gate now returns a redirect, so that stop never fires
kind: finding
state: closed
use-case: all capture; hard limits 6 and 9
session: fix-support-fetchgate-1
opened: 2026-10-21
closed: 2026-10-22

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

Integrator, at the merge (22 October 2026): the gate follows a redirect that stays on the host asked by default (three hops), so the within-host case this card feared (http to https, a trailing slash) does not set pages aside; what remains is the cross-host case, where the lanes' final-address stop no longer fires and a `HTTP 30x` row is set aside instead. Nothing is fetched from the other host either way.

Closed by redirects-1 (22 October 2026), one commit per lane: each guard now stops on
`f.status in fg.REDIRECT_STATUSES` with `f.location` off its host, its set-aside or log line and
its stop as before. No lane passes `follow=`: no source is known to chain past three same-host hops.
Each lane has a test injecting a `Fetched` with status 302 and a location on another host, seen
failing against the old guard; the four `final_url`-elsewhere tests (charities, courts, the
Authority, the Tribunal) were amended to that shape, building practitioners and tenders had none.
