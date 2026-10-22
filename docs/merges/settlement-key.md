# settlement-key: the settlement's key onto the board, the slow citation test repointed
branch: integrate/settlement-key (the integrator's own, from main at b3ae1b7)
session: integrator
raised: 2026-10-23

The column `pub.iwi_directory_settlements.settlement_key` was published at
the merge of `fix-registers-iwi-directory-1` (second sitting, 80f2dd3). At
that gate a catalogue field and a repointed test that read it were refused
(`UndefinedColumn`: the gate's full tier runs before its publish) and
reversed; this branch carries them now that the column is live: the board's
settlements view shows `settlement_key` beside each row, and
`products/scan/tests/test_templates_real.py` groups by `settlement_key` and
cites each row by its own key, so the test no longer skips.

## Result (integrator, 2026-10-23 12:27 NZDT)

Merged: `baf9cd5 merge integrate/settlement-key: gate green` (fast tier
green in 626 s; the board's fast tests and both real-data test files green
by hand first; the gate's staging step had nothing to load). The rule is in
`docs/briefs/next.md`: a column the gate publishes is catalogued and tested
at the next merge. Worker stopped for the window and started after the push.
