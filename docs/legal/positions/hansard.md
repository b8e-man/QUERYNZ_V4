# Parliament's Hansard (draft position, ruling 61)

hosts: hansard.parliament.nz, parliament.nz

Class: the official report of the debates of the House of Representatives
(Hansard), one transcript page per sitting day, cut into sections, with who
spoke. Lane: `registers/hansard`. Draft, held in the lane's folder because
the fence keeps a build session out of `docs/legal/positions/`; the
integrator moves it there. Written 26 October 2026 by hansard-1.

**Finding: the estate captures nothing from these hosts (ruling 78). What it
holds is the old estate's capture, exported once from its tables (ruling 96),
and, from hansard-2, the third-party MCP's index of which pages changed. The
gate must refuse both hosts: the integrator adds them to `HELD` in
`support/fetchgate` when it moves this page, since a `hosts:` line alone
would let the gate fetch them.**

1. **Is the page open?** It was. The old estate read the transcripts from
   17 July to 2 October 2026 (its `fetched_at`), sitting days 20 November
   2024 to 23 September 2026, with no login and, as far as its records show,
   no challenge. Since about 5 October 2026 the site answers automated reads
   with a challenge, which the estate never passes (hard limit 6). Arthur
   ruled on 21 October (78) that Hansard is not captured and no permission
   is asked; the updates come from his third-party source (ruling 96).
2. **Is storing it lawful copying?** The Copyright Act 1994, s 27(1), says no
   copyright exists in the debates of the House of Representatives, so
   copying and storing the text is not a copyright question. To confirm with
   the lawyer: the section's exact wording, and whether the roster and
   section titles the old estate added take any other protection (they are
   Parliament's own headings and names).
3. **What terms did we accept?** None by the estate: it fetched nothing. The
   old estate read the pages under its own rules (old ruling 242: a
   government source's proactively released information, politely). Not
   read here: parliament.nz's copyright and terms pages, which sit behind the
   same challenge. The MCP's terms are Arthur's to name (ruling 78); hansard-2
   records them before it joins the index.
4. **What does privacy law, or the statute, limit?** The speakers are Members
   speaking in their public role. A speech may name a member of the public,
   and a Member may, under privilege, name a person a court has suppressed.
   Parliamentary privilege protects the House's own record, not every
   republication: the Parliamentary Privilege Act 2014 protects fair and
   accurate reports of the House's proceedings, and the lawyer is asked
   whether showing the text whole on a sold product is such a report. Until
   then the text is shown only on the board (local network, hard limit 13),
   and a name the estate holds as suppressed is suppressed in it too (hard
   limit 16). Measured 26 October: 11 street-number-and-street strings in
   3,923 sections, none a person's home (road works, development sites, a
   commercial building, a hypothetical in a bill debate).

Crawl delay: none read (the robots file is behind the challenge). Floor:
none needed, nothing is fetched. Author: hansard-1, 26 October 2026.
