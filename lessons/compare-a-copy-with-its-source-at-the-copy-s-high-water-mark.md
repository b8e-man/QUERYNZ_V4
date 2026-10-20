Bring a copy of a live ledger level at every build and count its source only up to the copy's highest id: a copy made once goes red at the next row, and a version constant in the copier goes stale.
area: links, links.old, links.check, any copy of an old-estate ledger
paid-for-by: 2026-10-21, fix-links-1 (cards the-links-copy-the-old-ledgers-once-and-the-check-counts-them-live, the-old-estate-s-anchors-moved-to-weights-2-3-and-the-copy-calls-them-superseded)

The links copied the old estate's three ledgers once (20 October) and the
check counted them against the live old tables; one donor anchor at 03:33
the next day turned the check red, and the copier's `CURRENT_WEIGHTS =
"donor-anchor-2.2"` had already called 6,466 newer judgments superseded.
Now each build diffs the ids and withdrawals, copies what is missing, and
takes each donation's latest live row by id (never a version sorted as
text). The check counts the source up to the copy's highest id, so it
compares like with like, and names what was decided since.
