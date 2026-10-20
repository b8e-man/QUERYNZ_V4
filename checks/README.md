# checks — the checks board and the comparison with the frozen site

See `docs/plan/design.md` "How the code is laid out". May import `support`
and read published tables only.

- `board.py`: runs every registered check, writes `<live>/checks/board.json`,
  alarms on red, exits 1 on red. `--heartbeat` alarms if the board itself has
  not run in 26 hours; `--test-alarm` sends one test alarm.
- `frozen_product.py`: the first check (plan 1.6): the daily release was
  green, the old board ran, the site's mail, and a listing by path and hash
  of the captured documents at each new version (`<live>/checks/frozen-product/listings/`).
- `comparison.py` and `comparison_figures.py`: the comparison with the frozen
  site (plan 4.5). `python -m checks.comparison run` pairs today's frozen
  release with the rebuilt version built from its listing, reads every file
  of the ten kinds on both sides into the same figures (every section the
  template's `page_sections` lists; `sections_added` in
  `products/templates/ftm/ftm.json` is read so the shape's own keys are not
  counted), differs them with no tolerance on money, groups each difference
  by a cause that has a card in `cards/`, and writes
  `<live>/checks/comparison/days/<version>.json`, beside it every
  difference with its cause (`<version>.diffs.jsonl`, figures only), and the
  clean-day ledger `ledger.jsonl`. `show` prints the last day; `causes` lists
  the causes and their cards. A rebuilt page saying "not held" against a
  frozen page showing nothing is no difference. The board item reads the
  ledger. Its daily job is `qv4-site-compare` in the scheduler's catalogue
  (after `qv4-site-build`).
- `module_checks.py`: every lane's own check (`registers/*/check.py` with a
  main) and the board's and the published site's, run as commands with a
  timeout the way `windowed.py` runs track E's two; red on exit 1, a crash
  or a timeout. `python -m checks.module_checks` runs them all and times each.
- `release_compare.py`: two frozen versions file by file (plan 1.4).
- `jobs/`: the `qv4-` unit files. Installed on node2 by hand in 1.6; step 2's
  installer takes over and puts the same files on node1.

`<live>` is `/home/user/querynzv4-work/live`, outside git. Tests in `tests/`
run on fixtures and never touch the live old folder or the network.
