# scheduler: where step 2 stands

Last close: release-copy-1, 23 October 2026, node2. Branch
`session/release-copy-1`, merge request `release-copy-1`. Scope
`support/scheduler`, `support/installer`.

## Done

- Step 2 on one box (session 2, 18 October): the four founding jobs on the
  queue's clock, no `qv4-` timer left; the model server built from source
  beside the copy (`installer build`); `embed()` proven live.
- fix-support-scheduler-1 (23 October): a job new to the catalogue waits
  for its next slot.
- release-copy-1 (this close), the card's second half: the worker and
  every job run from the release copy `/home/user/querynzv4-release` (one
  pushed commit of origin/main, detached, its own `.venv`), moved by
  `python -m support.installer release` after every push; the catalogue
  reloads only at a commit of origin/main; the installer refuses the worker
  unit until the copy exists. Proven on a scratch clone of origin (made,
  rerun, refused an untracked file) and in tests that fail on their mutants.
  Nothing installed or restarted on the box; the copy is not made.

## Waits on the integrator, at the merge (node2, /home/user/querynzv4)

1. Push main, then `.venv/bin/python -m support.installer release`.
2. `.venv/bin/python -m support.installer apply --units --only qv4-worker@.service`.
3. With the worker idle: `systemctl --user restart qv4-worker@node2`; its
   journal names the copy and the commit.
4. Replace the stop/start interim in `docs/briefs/next.md`; close the card.

## Not done

- The product surfaces' units (`qv4-board`, `qv4-report`,
  `qv4-site-preview`, `qv4-scan`) still name the main checkout (outside
  this fence).
- The two-box proofs stay owed on node1 (cards/node1-setup-as-the-second-box.md).

## Next

The node1 setup card when Arthur powers node1.
