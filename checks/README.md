# checks — the checks board and the comparison with the frozen site

See `docs/plan/design.md` "How the code is laid out". May import `support`
and read published tables only.

- `board.py`: runs every registered check, writes `<live>/checks/board.json`,
  alarms on red, exits 1 on red. `--heartbeat` alarms if the board itself has
  not run in 26 hours; `--test-alarm` sends one test alarm.
- `frozen_product.py`: the first check (plan 1.6): the daily release was
  green, the old board ran, the site's mail, and a listing by path and hash
  of the captured documents at each new version (`<live>/checks/frozen-product/listings/`).
- `jobs/`: the `qv4-` unit files. Installed on node2 by hand in 1.6; step 2's
  installer takes over and puts the same files on node1.

`<live>` is `/home/user/querynzv4-work/live`, outside git. Tests in `tests/`
run on fixtures and never touch the live old folder or the network.
