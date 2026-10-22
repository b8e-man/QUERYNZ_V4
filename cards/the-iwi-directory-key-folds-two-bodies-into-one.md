# The iwi directory's key drops the macrons that tell Ngāti Hāua Iwi Trust from Ngāti Hauā Iwi Trust
kind: finding
state: closed
use-case: 14 the post-settlement governance map
session: scan-templates-2
opened: 2026-10-23
closed: 2026-10-23
module: registers/iwi_directory

An organisation's key is `tkm/org/` and its name folded (macrons off). Two
bodies print different names on their own iwi pages (stored pages
`53c9af4a…` and `5c4d374d…`, 23 October 2026): Ngāti Hāua Iwi Trust (Upper
Whanganui, a mandate recognised) and Ngāti Hauā Iwi Trust (Waikato, the
Ngāti Hauā Claims Settlement Act 2014). Both become
`tkm/org/ngati-haua-iwi-trust`, one entity row named for the first, listed
under both iwi, carrying both settlements. Of the nine bodies listed on more
than one page this is the only one whose pages print different names.

Template 3 shows it as the directory reads it (each settlement cited to the
page it came from) and says so in its limits. For the lane: key a body by
its name as printed, with its macrons (or by the page that lists it where the
names differ), and add the pair to the lane's hard cases. Fate at the next
checkpoint: fixed in the lane, or accepted onto the lane's limits.

Closed 2026-10-23 by fix-registers-iwi-directory-1 (second sitting). An
organisation's key stays its name folded (macrons off), except where its
pages print names that differ with the macrons kept: then each name printed
is its own body, keyed by the first page that prints it, and its relations
and settlements go with it (`load.split_by_printed_name`). On the full walk
of 22 October that is this pair alone: `tkm/org/ngati-haua-iwi-trust`
becomes `tkm/org/ngati-haua-iwi-trust/ngati-haua-upper-whanganui` (Ngāti
Hāua Iwi Trust, organisation, the mandate) and
`tkm/org/ngati-haua-iwi-trust/ngati-haua` (Ngāti Hauā Iwi Trust,
governance entity, the 2014 Act). One entity row changes key and becomes
two (2,696 to 2,697); its two "organisation of iwi" relations and two
settlement rows follow; no other entity, relation or settlement key moves.
The pair is in the lane's sample as a hard case, with a test on the stored
pages (it fails on the earlier load: one row named Ngāti Hāua, pages 2) and
one on invented pages (the same name on two pages stays one body).
