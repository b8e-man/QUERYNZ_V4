# Party boards as the parties declare them, on the board

**Not on the Follow the Money site** (ruling 72): this pane is the board's only surface until Arthur rules.

- **Roles read:** `select party, count(*), count(distinct name), count(distinct role) from pub.party_board_roles group by party`.
- **Pages:** `select status, count(*) from pub.party_board_pages group by status`; drop-notes by `reason` (the pages the profile's markers do not recognise, a theme's placeholder people, a layout the profile knows and does not pair). A page that was read and now drops is a site that changed its markup: the point, not noise.
- **Set aside:** `select reason, count(*) from party_boards.set_aside group by reason`: a vacancy, a name that repeats its role, a line the name rule refuses. Never the line's text.
- **A role row:** the party; the name as declared, and without its honorific beside it, with the bracket the page put after it (`(Acting)`, a place); the role as declared (several role lines joined by '; '), and whether the page states it beside the name or by the heading the name sits under; the section heading.
- **Citation:** the party's own page address, the day captured (first and last capture of the same bytes), the Archive's copy where it is one, and the page's hash. Source tier `declared`: the party's own claim on that day, which can be stale; not a register.
