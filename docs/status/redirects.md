# redirects-1: where it stands (22 October 2026)

Done. Six lanes' "redirected to another host: the run stops" guard read
`Fetched.final_url`, which the gate now sets to the URL asked, so it could
not fire. Each now stops on a 3xx (`fg.REDIRECT_STATUSES`) whose
`f.location` is off the lane's host, with its set-aside or log line and
its stop unchanged. One commit per lane on `session/redirects-1`:
building_practitioners, charities, courts, real_estate_authority,
tenancy_tribunal, tenders.

- `follow=` passed nowhere: no source is known to chain past the gate's
  three same-host hops.
- Each lane has a test injecting `Fetched(status=302, location=elsewhere)`,
  seen failing against the old guard. The four `final_url`-elsewhere tests
  (charities, courts, Authority, Tribunal) were amended to that shape;
  building_practitioners and tenders had none and gained one.
- `bin/fast` green on each lane; `tests/test_imports_one_way.py` green.
  Courts' run took 74.9 s against the 60 s target (most of it the sample
  fill); recorded by the tier, not a failure.
- Card `six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect`
  closed. Lesson filed:
  `lessons/when-a-producer-stops-setting-a-field-every-guard-on-it-passes-silently.md`.

Half-done: nothing. Next: the merge request `redirects-1`.
