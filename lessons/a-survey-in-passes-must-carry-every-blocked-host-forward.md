A survey run in passes must carry every host blocked or challenged in an earlier pass, and in its own run, into a skip list, or the next pass retries a challenged read.
area: capture, survey, fetchgate, hard-limit-6

Why: councils-1 surveyed 78 council sites in two passes (a sitemap pass, stopped as too slow, then a lean pass from
searched addresses). The lean pass reused the first pass's home pages only where one had landed, so it asked the
home pages of two councils the first pass had found behind a challenge (Imperva) once more, and after a 403 on one
council's home page it still asked that host's register page. And a block on `www.x.govt.nz` did not stop an ask of `x.govt.nz`: same site, another host string. The gate records each refusal but does not remember a
block across runs; the lane's own capture holds a host on its first block, the survey script did not.

In all, six asks went to a site already blocked; two answered 200, and the lane holds both sites anyway and does not use what came back.

How to apply: a survey script reads every earlier pass's log for `blocked` and keeps a set of hosts it never asks
again, adds to it the moment a read is blocked, and checks it before every request, keyed by site (the host without `www.`), not by the host string.
