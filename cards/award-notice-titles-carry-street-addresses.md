# Award notice titles carry street addresses
kind: finding
state: open
use-case: 10 tender and award intelligence
session: scan-templates-1
opened: 2026-10-21

`pub.award_notices.title` is the agency's own title of the tender. 754 of
the 29,874 are address-shaped by the scan's presentation rule 7 (a number
and a street word, or a street and a postcode): a school's or a site's
address mostly, but a housing agency's repair of one dwelling would put a
home's address in a published view (hard limit 15: "no published table
carries one"). The scan's first run of `tender-awards` was refused by rule
7 on 200 lines; the templates now title a notice by its agency and RFx ID
and never read `title`.

To decide, owner tenders: keep the title out of `pub` (the RFx ID finds it
on GETS), or publish it with address-shaped titles withheld and counted.
Read the 754 by eye first: how many name a dwelling. Nothing here was
printed beyond the count.
