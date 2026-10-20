# The links copy the old ledgers once and the check counts them live
kind: finding
state: closed
use-case: 1
session: founding
opened: 2026-10-21
closed: 2026-10-21

`links.build_all` skips `old.copy_ledgers` whenever `links.old_decisions`
already holds rows (`links/build_all.py` line 20), so the copy of the old
estate's three ledgers is the one made on 20 October at 10:22. `links.check`
then compares that copy's count with the old database's live count, which
grows: the old estate's donor-anchor job decided row 75929 at 03:33 on 21
October (the new ACT New Zealand declaration), and the check went red at the
09:00 reload, 71,319 copied against 71,320. Every further old decision widens
it, and a row the old estate later withdraws (`withdrawn_at`) is never
re-read.

Recommended: at each build copy the ledger rows above the copy's highest old
id and re-read `withdrawn_at` on the rows held (the ledgers are append-only,
so the copy stays a copy), and let the check compare like with like. Until
then the red is this card's. The lane's fix, not the integrator's.

Closed (fix-links-1, 2026-10-21): `links.build_all` now brings the copy
level at every build, after the rows and before the promotion:
`old.copy_ledgers` reads each ledger's ids and withdrawals, copies every
row the copy does not hold (above its highest old id, and any gap below),
re-reads `withdrawn_at` and `withdrawn_reason` on the rows held, and
`old.map_all` maps it onto the rows just gathered. `links.check` counts the
old table up to the copy's highest old id, withdrawals included, and names
rows decided since as `decided_since_the_copy`. Live, read-only, on this
branch's code: donor_anchors 71,319 = 71,319 (502 withdrawn each), row
75929 decided since; folds 5,479 = 5,479 (325 withdrawn); verdicts 381 =
381. Tests: `links/tests/test_old_ledgers.py`.
