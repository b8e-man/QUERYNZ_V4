# Whether a second worker (`qv4-worker@node2-b`) keeps running on node2 after the rehearsal
default: No: one worker per box is the design; `node2-b` is stopped at the close of the rehearsal and started again only for a drill. The two-box items are proven on the rehearsal record (18 October) and owed again when a second box exists.
blocks: Nothing
recommendation: The default. Two workers on one box share one memory reserve and one set of cards; the second brings no capacity, only a second claimant. A drill is one line: `systemctl --user start qv4-worker@node2-b.service` on node2.
raised: 2026-10-18 by scheduler (session 1)
