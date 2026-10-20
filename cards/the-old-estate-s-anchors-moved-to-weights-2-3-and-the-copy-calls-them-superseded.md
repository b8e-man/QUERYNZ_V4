# The old estate's anchors moved to weights 2.3 and the copy calls them superseded
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-21

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
