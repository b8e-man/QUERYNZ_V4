# fix-support-fetchgate-1 (second sitting): a block is known by its own page; Fetched carries the response headers and a 304 is "unchanged"
branch: fix/support-fetchgate-1 (pushed; 9f05438)
session: fix-support-fetchgate-1 (fix, support/fetchgate/)
raised: 2026-10-23
claims: support/fetchgate/__init__.py and its tests; the two cards below; lessons/a-word-on-a-page-of-content-is-not-a-challenge-a-block-is-known-by-its-status-header-title-and-size.md
closes: christchurch-s-infocouncil-listing-trips-the-gate-s-challenge-check (councils-1's), the-fetch-gate-returns-no-response-headers (societies')

This file is dated because `fix-support-fetchgate-1.md` is the first sitting's request, merged 2026-10-22
(3227953) and copied to `docs/merges/`. Copy this one beside it, not over it.

1. `looks_challenged` recognises a block by the block page's own landmarks: its status, its own header, its
   title (searched in the first 64 KiB), and only then a mark near the top, and only on a body no bigger than
   a challenge page (`CHALLENGE_PAGE_MAX` = 64 KiB). A word or a script name on a bigger page no longer makes
   it a challenge. The rule is one sentence in the docstring.
2. `Fetched.headers`: a plain dict with names as sent, default `{}`, added as the last field, so every
   positional `Fetched(...)` in the lanes' tests still builds. `Fetched.unchanged` is true on a 304. `open_url`
   returns a 304 with an empty body and never as a block, so a lane can send `If-None-Match` with the ETag it kept.

Tests: four new. The Christchurch shape (built from its size, links and where the word sits, never fetched)
fails on the old gate and passes now. The Cloudflare challenge and block pages and the Incapsula, Imperva and
Radware shapes, and a 900 KB page titled "Just a moment...", are still failed reads. The headers and 304 test
runs a loopback server: 200 with an ETag, then 304 when it comes back. Fast tier: `bin/fast support/fetchgate`
green in 42 s; whole repository green in 643 s (target 300 s missed, recorded). No lane or caller changed.

**What the integrator must do after the merge:**
- Clear the hold on Christchurch's instance by hand:
  `DELETE FROM council_minutes.capture_held_hosts WHERE host = 'christchurch.infocouncil.biz'` on `querynz_v4`
  (node2, the integrator's login). The next nightly councils run asks again. This session did not do it.
- Drop the line on the councils lane's known limits about Christchurch once that run lands its meetings.
- Nothing to install; no job changed.

Not done (outside the fence): the societies lane does not yet keep the ETag on its ask row or send
`If-None-Match`; that is the lane's own fix, now possible. `support/fetchgate` has no `spec.md` (the brief
named one); the module docstring stands in for it, as for the other support modules.
Lesson: one filed (first line 219 characters).

## Result (integrator, 23 October 2026 03:55 NZDT)

Merged into main as 9f59552 (`merge integrate/fix-support-fetchgate-1: gate green`). Branch `integrate/fix-support-fetchgate-1` from `fix/support-fetchgate-1` (9f05438; the launcher reused the first sitting's number because its branch was retired), main merged. Cards `christchurch-s-infocouncil-listing-trips-the-gate-s-challenge-check` and `the-fetch-gate-returns-no-response-headers` closed by the session; board, lessons index and queue regenerated. The hold on `christchurch.infocouncil.biz` cleared by the integrator's hand after the merge (one row deleted from `council_minutes.capture_held_hosts`; Hawke's Bay and Kāpiti stay held on their 404s); the next nightly councils run asks Christchurch again. Also at this merge: the two `pub.local_election_*` views catalogued on the board (local-elections-1's merge after). The first gate was refused by the board's outside check on those views, which the integrator should have catalogued before running it; the second gate green. Fast tier green in 665 s (target 300 s missed, recorded). Nothing installed; no job changed. Branches and worktree retired. Record copied beside the first sitting's as `docs/merges/fix-support-fetchgate-1-2026-10-23.md`.
