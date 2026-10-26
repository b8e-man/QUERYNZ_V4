# Hansard, on the board

**A sitting day's pane** (`pub.hansard_sittings`): the day, the Parliament and volume, whether the transcript was a
Draft or Corrected when the old estate read it, its sections, speech turns (member and role-only) and members, and
the transcript's address as the citation. Where the MCP's index names the
page, its last-modified and when the index saw it; a page modified after the old estate's capture says "the held text
may be older than the page" (on 27 October the index names none of the 137 pages: its pages are www.parliament.nz's).
Where the MCP holds the day's PDF, "also held as the daily PDF's text", linking to the day's pane.
Every row says "taken from the old estate's tables; original not held" and "held at 23 September 2026".

**A section's pane** (`pub.hansard_sections`): the proceeding, subject and bill, the text as captured, and its speech
turns in order. 262 sections were captured with no text and show "no text held". The text is shown on the board only
(local network, hard limit 13); a name the estate holds as suppressed is suppressed in it.

**A person's pane** (`pub.hansard_speeches`, by member id): the days and sections a member spoke in, how many turns,
on what proceeding and bill. The name shown is the old roster's, and the label beside it is the page's as the old
capture read it ("Hon BARBARA EDMONDS"), named "as read by the old estate". A turn is presence on the record, not
advocacy: the chair speaks often. Role-only turns (the Speaker, the chair, the Clerk, unnamed interjections) show the
role and never a person.

**A day's pane** (`pub.hansard_days`): the sitting day, the daily PDF's address as the citation, the provider's hash of
the PDF small beneath it, when the provider captured it, its pages and words. "Captured and read off-estate by the
query-nz provider (ruling 78); pdftotext's text, no section or speaker split." Where the old transcript holds the day,
"also held as the old transcript's sections", linking to the sitting's pane, with how many of its subjects the PDF's
text carries. The text is not in any view: the board's document opener shows the landed record whole (ruling 88,
local network only); a name the estate holds as suppressed is suppressed in it.
