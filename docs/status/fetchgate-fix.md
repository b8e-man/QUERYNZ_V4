# fix-support-fetchgate-1: where it stands

Done, 2026-10-21; merge request raised. Nothing half-done.

- `support/fetchgate`: Imperva's interstitial (title "Pardon Our Interruption", header
  X-SPA-INTERSTITIAL) is a blocked read. "reese84" is NOT a mark: the lesson
  `a-real-page-can-carry-the-challenge-script-...` holds, real pages load that script.
- `open_url` no longer follows redirects: it returns the 3xx with `location`. `follow=n` is the
  opt-in; each hop is checked, recorded and paced. `fetch` may return a 4th item, headers.
- Five new tests; each fails on the old gate. Fast tier green for support/fetchgate and all
  eleven caller modules; tests/test_imports_one_way.py green.
- Carded: `six-lanes-stop-on-final-url-but-the-gate-now-returns-a-redirect` (caller modules).

Next: the integrator merges; the six lanes take the card.
