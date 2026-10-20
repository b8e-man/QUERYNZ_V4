Before a template names a view in a section, check that a link can reach it (`pub.names` carries the view): a view no link reaches always prints "none found", which reads as a clear and is not one.
area: subject reports, products/templates, step 5.2 templates, flags
paid-for-by: 2026-10-20, recruitment session, step 5.2

The recruitment template first read `gazette_bankruptcies` and
`gazette_appointments` in its sections. Neither is in `pub.names`, so no
link rule joins a row of them to a person, and every report said "none
found in Gazette notices" for them: a board screen silently clearing every
candidate of bankruptcy. The fix in a template: drop a view no link reaches
(appointments), or keep it and make its rule blocked, never clear, with the
section's text saying so (bankruptcies); card the links lane. The same
holds for a rule's clear: the prohibition rule clears only when every
prohibition row is in `pub.names` (536 of 538, the two revoked) and the
walk read every link (`links_omitted` is 0), and blocks otherwise. Second
thing the checkpoint taught: a Gazette company notice of kind "removal" is
not insolvency; count insolvency by the notice's kind, or every struck-off
company reads red.
