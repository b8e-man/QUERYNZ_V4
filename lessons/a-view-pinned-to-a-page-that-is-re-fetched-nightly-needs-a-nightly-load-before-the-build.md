A view pinned to a page that is re-fetched nightly needs a nightly load before the build, timed after the release its check compares with, or its rows cite yesterday's hash.
area: lanes, published site, pin, scheduler, disclosures, jobs
paid-for-by: 2026-10-23, fix-registers-disclosures-1 (the 08:00 build left out 421 of 421 disclosure rows)

Rule: a lane whose published rows cite a page the old estate re-fetches
every night (the Commission's listings under `ec-donations/index/`: the
$20,000 and $30,000 tables, the by-year listing, the party register and
the logo applications are rewritten at 03:34) gets a nightly `--job` load
that runs after the frozen release and before `qv4-site-build`. The build
keeps only rows whose `document` is in the release listing, so rows loaded
from the previous night's bytes are all left out, however right they are.

Time the job after the release, not merely after the capture: a job that
publishes only when its check against the frozen site is green, checked
against the previous day's release, goes red on every day the source adds
a row. The frozen site's disclosure count rose on 21 and 22 October
(269, 270, 271), so a 05:30 NZDT run would have published nothing on two
of three days. Old timers are local time and new jobs are UTC: pick a UTC
time that falls between the release's end and the build in NZDT and NZST.

How to find them: `find .../index -newermt <today>` after 03:34 lists the
re-fetched pages; join each pinned view's `document` to `docs.names` and
look for those names.
