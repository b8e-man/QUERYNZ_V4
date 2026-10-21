# fix-support-fetchgate-1: the gate blocks Imperva's interstitial and stops following redirects unasked
branch: fix/support-fetchgate-1 (pushed; fcf1f8e)
session: fix-support-fetchgate-1 (fix, support/fetchgate/)
raised: 2026-10-21
claims: support/fetchgate/__init__.py and its tests; cards/six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect.md; lessons/urllib-follows-redirects-so-a-gate-that-judged-the-url-asked-must-stop-the-transport-following.md; docs/status/fetchgate-fix.md
closes: the-fetch-gate-misses-an-imperva-interstitial-and-follows-redirects-unasked (grants-1's, on session/grants-1)

1. Imperva's interstitial is a blocked read: "pardon our interruption" in
   CHALLENGE_MARKS, and a new CHALLENGE_HEADERS (`x-spa-interstitial`) read by
   `looks_challenged(status, body, headers=None)`. "reese84" was NOT added: the
   lesson `a-real-page-can-carry-the-challenge-script-...` says real pages from a
   protected site load the challenge script too; a test pins that.
2. `open_url` no longer lets urllib follow a 3xx. It returns the 3xx with
   `Fetched.location` (absolute, never fetched) and `final_url` = the URL asked.
   `follow=n` is the opt-in: every hop is checked against the positions (Refused
   if none names it), recorded and paced on its own host. No caller passes it yet.
   An injected `fetch` may return a 4th item, the headers; 3-tuples still work.

Tests: five new, each fails on the old gate (one runs a loopback server so the
real urllib path is proved, not a fixture). Fast tier green: support/fetchgate
and all eleven modules that call open_url; tests/test_imports_one_way.py green.

Carded, not done (outside the fence): six lanes stop on an off-host redirect
by reading `final_url`; that stop no longer fires, the URL is set aside as
HTTP 30x instead and the run goes on. Nothing is fetched from the other host.
Lesson: one filed (urllib follows by itself; test the real transport).

## Result (integrator, 2026-10-22 00:45 NZDT)

Merged into main as 3227953 (`merge integrate/fix-support-fetchgate-1: gate green`). Branch `integrate/fix-support-fetchgate-1` from `fix/support-fetchgate-1` (fcf1f8e), main merged. Imperva's interstitial is a blocked read (its title, its header, the reese84 script), so a page like it is a failed read and never landed as a document (hard limit 6); the gate no longer follows a redirect unasked, handing back the status and the address so the caller asks the gate about the new host, with `follow=` for a caller that wants each hop judged. The card it closes, `the-fetch-gate-misses-an-imperva-interstitial-and-follows-redirects-unasked`, is grants-1's and closed here. Integrator's amendment on the branch: a redirect that stays on the host asked is followed by default (up to three hops, each judged and paced as any URL; `same_host_hops=0` turns it off), because the session's own note said a within-host redirect (http to https, a trailing slash) would otherwise be set aside on every lane tonight; a redirect to another host is still returned unfollowed, with a test for all three cases. The card `six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect` stands for the cross-host case. The fast tier was first red on one grants mutant (the lane's own interstitial marks dropped): the gate now carries those marks, so the mutant is no longer a fault and was left out with the reason. Fast tier then green in 502.0 s. The three grants board views carried on this branch. Gate green; the staging step re-read the grants lane, whose first capture the scheduler had run meanwhile: 178,729 grants published in 8 s. Branches and the working copy retired.
