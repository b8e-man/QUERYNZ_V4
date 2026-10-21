# ministers-diaries: where it stands

**Date:** 2026-10-21, 18:10 NZDT. **Session:** `diaries-1` (Opus). **Step:** 6.2 template 4(a),
`registers/ministers_diaries/`. **Merge request:** none: BLOCKED at capture (card
`the-beehive-s-wall-refuses-the-diaries-reader`). Branch `session/diaries-1` pushed.

## The four questions (hard limit 4), as far as read

1. **Open?** Published on www.beehive.govt.nz, no login, but behind an Incapsula wall. Plain
   requests get the wall's shell. A real headed browser got the home page with no challenge, then
   was refused (403, the wall's incident page) on `/advanced_search` and a minister's page. Failed
   reads, logged, stopped (hard limit 6). Seven requests in all.
2. **Lawful copying?** Not yet read: `/copyright`. Diaries are a Crown proactive release (Cabinet,
   December 2018).
3. **Terms accepted?** None clicked; `/legal` not yet read.
4. **Privacy?** The policy leaves out home addresses as meeting places and personal, party and
   constituency business; releases redact under the OIA. The lane keeps names as printed (a public
   role at most), a location only as a place of business, redactions kept and counted.

## Held

- Draft position `position/ministers-diaries.md` (the gate reads it; integrator moves it).
- `browser.py`: the headed reader, gated by `fg.check`, five seconds apart, never reloads a refusal.
- `tables.sql`: capture tables only. No profile, reader, publish, check or sample yet: the layout has
  not been seen, and a profile is measured on real releases.
- Policy facts (the Beehive's release of 10 Dec 2018, in the old news store): January 2019 onward,
  monthly, within 15 business days; ministers and under-secretaries. Nothing exists for 2017.

## Next

1. One off-peak attempt (a hand run at 22:00 or later, four pages: `/copyright`, `/legal`,
   `/ministers`, one minister's page), stopping on the first refusal.
2. Served: listing, a sample of releases, profiles by shape, the reading, publish, check, tests.
3. Refused: Arthur's queue item `may-we-ask-the-beehive-to-let-the-diaries-reader-through`.

## Ruling 78 (21 October, 18:20)

The Beehive and Hansard are not captured; Arthur has a third-party source. The blocker card and the letter question closed with the ruling; the lane's browser, tables and draft position left the branch at the merge. Next: Arthur names the source; its position (ruling 61), then the register from it.
