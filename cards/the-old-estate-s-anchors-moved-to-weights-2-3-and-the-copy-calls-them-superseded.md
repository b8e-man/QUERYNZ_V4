# The old estate's anchors moved to weights 2.3 and the copy calls them superseded
kind: finding
state: closed
use-case: 1
session: founding
opened: 2026-10-21
closed: 2026-10-21

`links/old.py` names `CURRENT_WEIGHTS = "donor-anchor-2.2"`, and every
donor-anchor row at another version is mapped as "superseded (weights …) in
the old estate; not applied" (lines 239 to 260). The old estate moved to
`donor-anchor-2.3` on 30 September: 6,466 anchors carry it, decided 30
September to 21 October, against 9,025 at 2.2 (8,523 not withdrawn, decided
7 to 30 September). So the newest reading of each donation the old estate
re-decided is dropped and the older one kept, and a donation first anchored
after 30 September has no old decision applied at all.

Recommended: take the current version from the old table itself (the
version of its latest decision), or apply each donation's latest
non-withdrawn decision whatever its version, and record which versions were
seen. A lane fix; the figures above are the 21 October reload's.

Closed (fix-links-1, 2026-10-21): `CURRENT_WEIGHTS` is gone. Each
donation (its `source` and `row_key`) takes its latest live judgment,
the highest old id, whatever its version; older ones are "superseded by
<old id> (weights …)". Rows of 1.0 and 1.1 carry no `row_key` and are
never the word. A hold applies while the anchors it read at its version
are still applied. The map's tally records the versions seen and the
latest decision's version (donor-anchor-2.3 today). On the live ledger,
read-only: 2.3 has 6,466 rows, 6,235 applied (727 accept or
corroborated); 2.2 has 9,025 rows, 8,523 live, 1,938 applied (35 accept
or corroborated, on donations 2.3 has not re-judged). All 644 2.2
accept or corroborated rows already promoted agree with their 2.3
re-judgment, so no promoted decision is contradicted. 118 of the 127
2.2 holds read anchors that 2.3 has re-judged, so they no longer apply
(the old estate's own rule: a new run is a new read). The 2.2 and 2.3
figures are in `links/tests/test_old_ledgers.py`, which fails on any
hard-coded version (checked against 2.2 and 2.3).
