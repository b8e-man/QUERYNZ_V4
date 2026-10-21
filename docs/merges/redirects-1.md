# redirects-1: six lanes stop on a redirect off their host by its Location
branch: session/redirects-1 (pushed; 2653816)
session: redirects-1
raised: 2026-10-22
claims: registers/{building_practitioners,charities,courts,real_estate_authority,tenancy_tribunal,tenders}/capture.py and their tests (one commit per lane: 31b4ca3, e6c4b60, 5b84f9b, 1a361b9, c2e20a9, 75c1810); cards/six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect.md closed; one lesson; docs/status/redirects.md (2653816)

Since fix-support-fetchgate-1 the gate returns a redirect to another host
unfetched, in `Fetched.location`, with `final_url` the URL asked. The six
lanes' stop tested `final_url`, so it never fired: an off-host 302 was set
aside as "HTTP 302" and the run went on. Each guard now stops on a 3xx
whose `location` is off the lane's host, its line and stop unchanged.
No `follow=` anywhere: no source is known to chain past three same-host hops.

Each lane has a test injecting a 302 with a Location on another host, run
against the old guard and seen failing. The four tests that injected a
`final_url` elsewhere were amended to that shape (the gate no longer
produces it); building_practitioners and tenders had no redirect test.

Fast tier green on each lane; tests/test_imports_one_way.py green. Courts
took 74.9 s against 60 s (mostly the sample fill), recorded by the tier.
No network in any test; nothing fetched from any host.
Lesson: lessons/when-a-producer-stops-setting-a-field-every-guard-on-it-passes-silently.md

## Result (integrator, 2026-10-22 02:29 NZDT)

Merged into main as bd35af5 (`merge integrate/redirects-1: gate green`). Branch `integrate/redirects-1` from `session/redirects-1` (2653816), main merged. The six lanes (building practitioners, charities, courts, the Real Estate Authority, the Tenancy Tribunal, tenders) stop on a redirect to another host by `Fetched.location`, one commit each with a fixture test that fails without it; the card `six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect` closed by the session; the lesson filed. Fast tier green in 529.5 s. Gate green; the staging step reloaded the touched lanes from their held passes: building practitioners 786 rows, charities 1,066,289 rows in 50 s, courts 148, tenders 61,138; the Real Estate Authority and Tenancy Tribunal lanes stay held (nothing published). Branches and the working copy retired.
