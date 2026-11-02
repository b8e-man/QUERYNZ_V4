# lobbying-meetings-suppliers: known limits and the checkpoint

Step 8.5 (use case 15, lobbying; step 6.2's template 4, parts (a) and (b)). Part (a), the ministers' diary register, is
`pub.minister_diary_entries` (ruling 78's source, 208,464 entries). Part (b) here: each meeting resolved to the companies
register by the company's whole name, and the company's awards on the GETS file beside it.
26,958 lines on 2 November 2026 (the award step optional: a company met that won no award is a line too).

## Known limits

The template's `limits` are the full list. In short: ministers only; a meeting joins a company only where the whole
attendees text is the company's name (13,207 of 208,464 entries on 2 November 2026's evening tables; lobbying-attendees-suppliers starts from each attendee instead); every line is near and a
generic name gives a namesake's line; an address-flagged entry is never read; nothing says why a meeting was held.

## Part (c), not built

The legislation join (minister, portfolio, bill, Hansard speech, the meetings beside it by date) is not built: it needs a
bill register (none is published) joined to `pub.hansard_speeches` by bill, and the portfolio-to-bill map. Its size: the
four registers are held but for the bills; one lane and one template.
