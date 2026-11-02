# lobbying-attendees-suppliers: known limits and the checkpoint

Step 8.5 (use case 15, lobbying; step 6.2's template 4, parts (a) and (b)), started from each attendee of a meeting
(`pub.minister_diary_attendees`, the diaries lane's split of each entry's attendees text, by rules) rather than from the
whole attendees text, as lobbying-meetings-suppliers does. Each attendee's organisation part resolved to the companies
register by the company's whole name, and the company's awards on the GETS file beside it.

## Known limits

The template's `limits` are the full list. In short: ministers only; a meeting joins a company where one attendee's
organisation part is the company's name (11,864 of 208,464 entries, 5,631 of them past the whole-text join, measured 2
November 2026); the Crown's own bodies, bare roles, groups with no body's name and persons with no organisation are not
read; every line is near and a generic name gives a namesake's line; an address-flagged entry is never read; nothing says
why a meeting was held.

## Not run yet

The view `pub.minister_diary_attendees` is published by the diaries lane at its merge; the scan runs after it. Proved on 2
November 2026 on the live tables with the view stood in from a scratch build of the lane: 31,969 lines, all near, 14,870 of them a namesake's; 11,864 entries; 3,823 companies; the presentation rules found no problem on any line.
