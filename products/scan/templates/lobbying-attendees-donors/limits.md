# lobbying-attendees-donors: known limits and the checkpoint

Step 8.5 (use case 15, lobbying; step 6.2's template 4, part (b)), started from each attendee of a meeting
(`pub.minister_diary_attendees`, the diaries lane's split of each entry's attendees text, by rules) rather than from the
whole attendees text, as lobbying-meetings-donors does. Each attendee's organisation part resolved to the companies
register by the company's whole name, and a party-return donor filed under the company's name beside it (near).

## Known limits

The template's `limits` are the full list. In short: ministers only; a meeting joins a company where one attendee's
organisation part is the company's name; the Crown's own bodies, bare roles, groups with no body's name and persons with
no organisation are not read; every line is near; the donor is the Commission's; nothing says why a meeting was held or
that a donation and a meeting have anything to do with each other.

## Not run yet

The view `pub.minister_diary_attendees` is published by the diaries lane at its merge; the scan runs after it. Proved on 2
November 2026 on the live tables with the view stood in from a scratch build of the lane: 118 lines, all near; 73 entries; 14 companies; the presentation rules found no problem on any line.
