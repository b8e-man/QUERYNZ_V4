# A settlement's key in the iwi directory names several rows, one per body
kind: finding
state: open
use-case: 14 the post-settlement governance map
session: scan-templates-2
opened: 2026-10-23
module: registers/iwi_directory (products/board reads the same view)

`pub.iwi_directory_settlements.key` is the settlement's (`tkm/settlement/<act>`),
and there is one row per body whose entry names it, each read from that
body's page: the Central North Island collective is 8 rows under one key,
the two Te Tau Ihu Acts of 2014 are 3 and 4, and the key
`tkm/settlement/post-treaty-settlement-governance-entity` (2 rows) is the
flag's own words read as a settlement's name. 110 rows, 97 keys.

The scan numbered a citation by view and key, so 13 lines cited another
body's page, and its check passed because the key exists. Fixed in the
shape (blocker `the-scan-templates-2-shape-diff-at-the-merge`: a citation is
the row's key and its document, page and place, and the check reads the
document back). Open for the lane: give each row its own key (the entity's
key with the settlement's) and keep the settlement's as a column; and read
the generic flag text as no settlement name. The board's settlements join
by entity key and is not affected; a board page addressed by this key would
be. Fate at the next checkpoint: fixed in the lane or accepted onto its limits.
