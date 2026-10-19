# The installer does not reach a product's unit folder
kind: blocker
state: open
use-case: -
session: board
opened: 2026-10-20
closed:

`support/installer` places every `qv4-*.service` and `.timer` the repository
ships, but its `UNIT_GLOBS` name `checks/jobs/` and `support/*/units|jobs/`
only. The board's standing service is `products/board/units/qv4-board.service`
(plan 4.9: "on its own port, on the local network only"; the plan's design
rule 7: every product's surface is a web app on its own port). `support/` is
outside the board fence.

After the merge of `board-1`, the integrator adds two globs to
`support/installer/__init__.py` (and the installer's test that lists them):

```python
"products/*/units/qv4-*.service", "products/*/units/qv4-*.timer",
```

then runs `python -m support.installer units` on node2 and
`systemctl --user enable --now qv4-board.service`, and runs
`python -m products.board state` once from the main checkout (it creates
`board.pins` and `board.paths` in `querynz_v4`; idempotent). The board then
answers on `http://10.0.0.2:8420/` (and `127.0.0.1:8420` on the box). Until
the unit is placed the desktop launcher still works: its `open` script falls
back to starting the board from the main checkout in the background.
