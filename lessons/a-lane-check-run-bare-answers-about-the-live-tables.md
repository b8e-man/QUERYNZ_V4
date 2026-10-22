A lane's check run bare is what the board runs, so its defaults name the live schema in querynz_v4 and the reader login; a session's scratch proof is the switch, never the default, or the board reads a scratch schema that has gone.
area: registers, checks, module-checks, board, charities
paid-for-by: 2026-10-23, fix-registers-charities-1, the board red every morning since 20 October

`registers/charities/check.py` defaulted `--schema` to `scratch_charities_full`
and `--database` to `querynz_v4_sample`, the build session's own proof. The
board's module-checks run every lane check with no arguments, so from the
day the scratch schema was dropped it crashed with UndefinedTable and the
board never once saw the live charities tables. Sibling lanes
(`iwi_directory`, `grants`) default to the live schema and `querynz_v4` and
choose the read-only login there. Two more things to hold when writing
one: the reader has no grant on a lane's `_private` twin, so a check reads
only the lane's own schema and `pub.`; and a missing table is a red line
with a reason, not a traceback. Test the bare `main` with a stand-in
`db.connect` that records which login and database it was asked for.
