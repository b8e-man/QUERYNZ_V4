# Hansard, on the board

**A sitting day's pane** (`pub.hansard_sittings`): the day, the Parliament and volume, whether the transcript was a
Draft or Corrected when the old estate read it, its sections, speech turns (member and role-only) and members, and
the transcript's address as the citation. Where the MCP's index names the
page, its last-modified and when the index saw it; a page modified after the old estate's capture says "the held text
may be older than the page" (on 27 October the index names none of the 137 pages: its pages are www.parliament.nz's).
Where the MCP holds the day's PDF, "also held as the daily PDF's text", linking to the day's pane, with the split's
section and member-turn counts beside the old estate's.
Every row says "taken from the old estate's tables; original not held" and "held at 23 September 2026".

**A section's pane** (`pub.hansard_sections`): the proceeding, subject and bill, the text as captured, and its speech
turns in order. 262 sections were captured with no text and show "no text held". The text is shown on the board only
(local network, hard limit 13); a name the estate holds as suppressed is suppressed in it.

**A person's pane** (`pub.hansard_speeches`, by member id): the days and sections a member spoke in, how many turns,
on what proceeding and bill. For the 137 days the old estate holds, the name shown is the old roster's and the label
beside it is the page's as the old capture read it ("Hon BARBARA EDMONDS"), named "as read by the old estate". For
every other day the MCP holds (1,725 on 31 October 2026, 2003 to 2026), the turns are the split's (`turns_from` says
which): the speaker line as printed in the daily PDF, its party and electorate or role in brackets, the member from
the old roster within that day's Parliament, named "the split of the daily PDF's text (hansard-day)". A turn is
presence on the record, not advocacy: the chair speaks often. Role-only turns (the Speaker, the chair, the Clerk,
unnamed interjections) show the role and never a person; a chair named in brackets ("CHAIRPERSON (Barbara Kuriger)")
shows the role and the member.

**A day's pane** (`pub.hansard_days`): the sitting day, the daily PDF's address as the citation, the provider's hash of
the PDF small beneath it, when the provider captured it, its pages and words. "Captured and read off-estate by the
query-nz provider (ruling 78); pdftotext's text; split into sections and speaker turns by the estate's own rule
(profile hansard-day), no model." Its layout (final or draft), Parliament, sections, turns, member turns and
members, and the text reader's state: read (with its pieces and the names found), waiting, or set aside with the
reason. Where the old transcript holds the day, "also held as the old transcript's sections", linking to the
sitting's pane. The text is not in any view: the board's document opener shows the landed record whole (ruling 88,
local network only); a name the estate holds as suppressed is suppressed in it.

**A day's sections** (`pub.hansard_day_sections`): under the day's pane, each section the split made: the heading as
printed, the proceeding, subject and bill, its turn counts; a note says whether these turns are the ones published
(the old transcript does not hold the day) or held beside the old estate's for the comparison.

**A name's pane** (`pub.hansard_people`): a person or body a speaker named in a speech, as the text reader read it:
the name as printed, its kind (person, company, agency, body, other), the role as the text says it, the organisation
a person is "of" where the text says, the day, the section and the piece of the day's reading it came from, with the
model and reader that read it. "Named in a speech as the text reader read it; the speaker is the turn's row." Never a
link and never a claim: the links lane reads the view (ruling 123). A name the estate holds as suppressed is
suppressed here as on every surface (hard limit 16).
