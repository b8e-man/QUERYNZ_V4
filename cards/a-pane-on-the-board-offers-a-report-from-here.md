# A pane on the board offers "report from here"
kind: finding
state: open
use-case: subject report (5.1); the board (4.9)
session: report
opened: 2026-10-20

The report's page takes a ref as the board names a row (`register:key`),
and every line of a memo links back into the report (`/report?ref=…`), but
a board pane has no link out to the report. A one-line fix in
`products/board/panes.py`: on a row pane, beside "person: the group and
namesakes", a link to `http://10.0.0.2:8440/report?ref=<register>:<key>`
(the address a setting, `QV4_REPORT_URL`, as the report's page takes
`QV4_BOARD_URL`). The board's status file named this as its step 5 item.
A fix session on `products/board` once `report-1` is merged and
`qv4-report` is enabled.
