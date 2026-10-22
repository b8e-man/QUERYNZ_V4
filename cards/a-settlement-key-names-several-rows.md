# A settlement's key in the iwi directory names several rows, one per body
kind: finding
state: closed
use-case: 14 the post-settlement governance map
session: scan-templates-2
opened: 2026-10-23
closed: 2026-10-23
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

Closed 2026-10-23 by fix-registers-iwi-directory-1 (second sitting). Each
row of `pub.iwi_directory_settlements` now has its own key, the entity's
with the settlement's (`<entity key>|<settlement key>`, e.g.
`tkm/org/raukawa-settlement-trust|tkm/settlement/central-north-island-forests-iwi-collective-settlement`),
and the settlement's key is kept beside it in a new column,
`settlement_key`, shared by every body whose entry names it. The flag's own
words with nothing beside them ("Post-Treaty settlement governance
entity.", Hako Tūpuna Trust and Ngāti Porou ki Hauraki Rūnanga Trust) are
no settlement: name and `settlement_key` blank, stage `settled: none
named`. Measured on the full walk of 22 October in scratch: 110 rows, 110
keys, 96 settlement keys (the Central North Island collective is one
`settlement_key` over 8 rows). The lane's check goes red on a row keyed
other than by its entity and settlement, or named by the flag's words; a
rule, two mutants and a test on the stored pages (Ngāti Hako added to the
sample) hold it. The view's other columns are unchanged; the board's join
(by `entity_key`) is unaffected; the six settlement-map scans re-cite at
their next run.
