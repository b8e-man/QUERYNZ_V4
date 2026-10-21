# The officers reach follows an officer's confirmed group only, so a director the links lane joins by name alone shows no other company
kind: finding
state: closed
use-case: 12 property developer due diligence; 11 healthcare; every template naming `officers`
session: property-1
opened: 2026-10-21
closed: 2026-10-21

`walk.follow_officers` lists the rows of each officer's confirmed group.
A director whose other directorships the links lane joins only near
(`name-only@1`: a name with no middle name, say) reaches nothing, and the
project history of the company the buyer asked about is empty. Measured
2026-10-21: of 12,719 current directors of registered companies named
"develop…", 4,602 have no confirmed link to another director row, and
1,956 of those have a near link to one. The checkpoint met it on GORING
DEVELOPMENT LIMITED (companies/9429050618637): its one director, Wenfeng
SU, sits on ROBERTON and KERVIL DEVELOPMENT LIMITED, both in liquidation,
and the report shows neither.

The template blocks `history-reach` and says so, and the serial pattern
stays blocked, never clear. For the report lane: list an officer's near
links one step too, near with the link's own reason after the officer's
(as `near` lists the start's), under the same officer limits, so a reader
sees a namesake's companies set apart rather than nothing. Prominence is
not a reason either way; the reason shown is the link's.

Closed (fix-report-2, 2026-10-21). `walk.follow_officers` lists, after the
rows of each followed officer's confirmed group, the rows the officer's own
near links reach (`pub.links`, grade near), each near with the officer's
reason first and the link's own after (`NEAR_OFFICER_LINK`), carrying the
link's rule, evidence, watch and decision, marked `near_link`; its company
and the notices on that company follow with the same grade, under the same
officer limits (`officer_rows`), and near links past the links limit are
counted in `links_omitted`. The memo says the row came by the officer's
near link. Prominence plays no part: the reason shown is the link's.
Fixture test `tests/test_reaches_2.py` (a mutant with no near links lists
nothing); `python -m products.report check` takes a near link between two
current directors of different companies from the tables at run time and
fails if the other company is not listed with the link's rule and reason.
On GORING DEVELOPMENT LIMITED today the director's one near link
(`name-only@1`) reaches PJO CONSTRUCTION LIMITED, in liquidation, now
listed in the property template's history section with its notice; no link
in today's `pub.links` joins the director to ROBERTON or KERVIL, which is
the links lane's. The property template's `history-reach` flag and serial
pattern can now read these rows: carded in
`the-property-template-can-now-read-the-charities-register-and-the-reaches`.
