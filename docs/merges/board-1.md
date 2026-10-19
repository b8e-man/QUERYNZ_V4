# board-1: step 4.9, the board: one search across every register, panes left to right
branch: session/board (pushed; head e1cc60b, on main at c5c30dc)
session: board (Fable)
raised: 2026-10-20
claims: products/board/ (catalogue.py, search.py, db.py, panes.py, server.py, links_view.py, state.py, check.py, tables.sql, __main__.py, spec.md, units/qv4-board.service, qv4-board.desktop, open, tests/); cards/the-installer-does-not-reach-a-product-s-unit-folder.md, cards/expense-release-totals-has-no-stable-key.md, cards/how-links-names-a-register-row.md; lessons/a-shared-read-role-s-connection-cap-counts-every-session.md; docs/status/board.md

**Ready to merge.** The board is a server-rendered page from the standard
library (no npm, no script): one search across the 35 `pub` views, results
grouped by register with a count each, "none found" and "not held" said;
a pane per row with its fields, dates as filed, the same register's rows,
links (confirmed first, near after, each with rule and reason, from
`pub.links`/`pub.groups`/`pub.decisions` once links/ publishes them; until
then every pane says "no links built yet"), namesakes by name alone listed
apart, and the document cited by hash, page, place and its names in the
store (never opened: captured documents carry addresses); panes chain left
to right as the path walked; a person pane; a pane pinned, a path saved
(`board.pins`, `board.paths`, only ever added to). Each view appears as its
lane's `pane.md` says (`catalogue.py`). A suppressed name, a revoked
prohibition's name, a withheld real-property text are never shown and never
matched by name; the only address view is the company's registered office.

Fast tier: `products/board` 25 tests green with the five-second rule;
`tests/test_imports_one_way.py`, `test_reading_limits.py` green. The whole
repository's fast tier is green except `tests/test_generators.py::
test_the_committed_records_generate_cleanly` (the card board and lessons
index not yet listing this session's three cards and lesson: generated at
the merge, as every lane request has reported). Slow (`tests/test_real.py`,
3 tests) green against the real published tables through the session
reader. Outside check `python -m products.board check` green: it also ran
the plan's done-when walk by name (donor → company → director), each pane
with a citation; by link once links exist.

**Nothing live was touched.** State was tried in
`querynz_v4_sample.scratch_board` (one pin, one path); the server was run on
127.0.0.1:8421 for the test only and stopped. Scans run on the product
reader (`QV4_PRODUCT_URL`, pub only, three connections); one session-reader
connection per page; the two writes through the owner.

After the merge, the integrator:
1. Card `the-installer-does-not-reach-a-product-s-unit-folder`: adds
   `products/*/units/qv4-*.service|timer` to `support/installer`'s
   `UNIT_GLOBS` (and its test), runs the installer's `units` step,
   `systemctl --user enable --now qv4-board.service`, and once
   `python -m products.board state` from the main checkout (creates
   `board.pins`, `board.paths`; idempotent). Then `http://10.0.0.2:8420/`.
2. Regenerates the card board and lessons index.
3. Passes `expense-release-totals-has-no-stable-key` to the expenses lane
   and `how-links-names-a-register-row` to the links session.

## Result (integrator, 2026-10-20 07:55 NZDT)

Merged into main as 3918dd3 (merged main first). Done at the merge: the
installer reaches `products/*/units/` (two globs, the prefix scan, a
test; its card closed); board and lessons index regenerated. Fast tier
and gate green. After the merge: `qv4-board.service` installed with
`python -m support.installer apply --units --only qv4-board.service`,
enabled and started; `python -m products.board state` run once; the
page answers 200 on `http://127.0.0.1:8420/` (and `10.0.0.2:8420` on the
local network). Arthur has the desktop launcher line. The two finding
cards go to their lanes (expenses: a stable key for the release totals
view; links: how a link names a register row). The session ran headless
from the integrator as Fable, about 45 minutes; it raised its request
before its commit and push, which followed a minute later.
