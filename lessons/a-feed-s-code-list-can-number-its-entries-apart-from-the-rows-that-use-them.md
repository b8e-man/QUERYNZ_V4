Resolve a feed's codes against the source's own resolved view before trusting its code list: the Charities Register's MainSector, MainActivity and MainBeneficiary lists hold the right names under other ids than its organisation rows carry.
area: charities, odata, code lists, reading a register, outside check
paid-for-by: 2026-10-21, charities-b session, step 4.1

Decoded through the `MainSector` list, the 9,521 charities filed under sector
7 were "Emergency / disaster relief" and the 7,780 under 15 "Economic
development". The register's own `vOrganisations` view, which carries the same
ids on every one of 46,138 rows, names them "Education / training / research"
and "Religious activities"; it disagreed with the list on 42,763 sectors,
33,724 activities and 37,748 beneficiaries. Same names, renumbered (the view's
ids run nearly alphabetically). Nothing in the list, the metadata or the data
dictionary says so; a check against the view found it on the first full build.

How to apply: when a source publishes both codes and a view that names them,
compare the two over every row before choosing the decoding, keep the
comparison as a check that can go red, and look at the distribution (the most
common sector being disaster relief should have been a question).
