# ministers-diaries: where it stands

**Date:** 2026-10-21, 16:40 NZDT. **Session:** `diaries-1` (Opus). **Step:** 6.2 template 4(a),
`registers/ministers_diaries/`. **Merge request:** not yet raised.

## The four questions (hard limit 4), as far as read

1. **Open?** The releases are published on www.beehive.govt.nz with no login. The host sits behind
   an Incapsula wall: a plain request gets the wall's shell (robots.txt and the sitemap, 21 Oct).
   A real headed browser was served the home page with no challenge; then `/advanced_search` and a
   minister's page were refused (403, the wall's incident page). Failed reads, logged; the run
   stopped. One more off-peak attempt tonight at 22:00, four pages, stopping on the first refusal.
2. **Lawful copying?** To read: the site's `/copyright` page (tonight). Ministerial diaries are a
   Crown proactive release under the Cabinet policy of December 2018.
3. **Terms accepted?** None clicked; `/legal` to read tonight.
4. **Privacy?** The policy itself leaves out home addresses as meeting places, personal, party and
   constituency business, and anything that would breach personal privacy; releases redact under
   the Official Information Act. Kept: names as printed, a public role at most; a location only as
   a place of business; redactions kept and counted.

## Done

- Draft position `registers/ministers_diaries/position/ministers-diaries.md` (gate reads it).
- `browser.py`: the headed reader, gated and paced, stops on a refusal.
- Policy facts from the Beehive's own release of 10 Dec 2018 (held by the old news store): diaries
  from January 2019, monthly, within 15 business days; ministers and under-secretaries.

## Next

1. Tonight's pass; if refused, the lane is blocked at capture and goes to Arthur.
2. If served: the listing, a sample of releases, then the profiles and the reading.
