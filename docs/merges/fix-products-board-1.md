# fix-products-board-1: every pane offers "report from here"
branch: fix/products-board-1 (pushed; 40e244e)
session: fix-products-board-1 (Opus, fix weight)
raised: 2026-10-20 (written into the inbox by the integrator from the session's closing report: the scope hook refused the fix copy's write to the inbox link; carded `a-fix-session-cannot-write-its-merge-request-into-the-inbox`)
claims: products/board/ (panes, server, spec.md, tests/test_panes.py, units/qv4-board.service); card `a-pane-on-the-board-offers-a-report-from-here` (board half closed; the card closed)

Every row pane and person pane carries one "report from here" link to
`<QV4_REPORT_URL>/report/<register>:<key>`, shown only when the
environment names a report server; the unit sets
`QV4_REPORT_URL=http://10.0.0.2:8440`; spec.md says so; a test in
`test_panes.py` fails without the link. The board's fast tier green
(27 s); the reading-limit and one-way import tests green. On the real
data on a spare local port a candidate's row pane and person pane each
showed the link.

For the integrator: the address exists once `report-2` is merged; restart
`qv4-report` after that merge (its running catalogue predates the
recruitment template's views and `/report?ref=` errors today); reinstall
and restart `qv4-board` for the new setting; the card file collides with
`report-2`'s copy of the same card: take this branch's, which carries
`report-2`'s paragraph word for word and adds the board's.

## Result (integrator, 2026-10-20 17:30 NZDT)

Merged to main at bbba72b, gate green. The card took this branch's copy.
`qv4-board` reinstalled with the report address and restarted; a row pane
on the live board carries the "report from here" link to 10.0.0.2:8440.
`qv4-report` was restarted on report-2's merge earlier. Worktree and branch
retired.
