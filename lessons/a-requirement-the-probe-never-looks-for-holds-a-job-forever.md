A job's `requires` must name programs in the probe's PROGRAMS list; a name the probe never looks for reads as missing, the job is never eligible, and the worker says nothing. Test: every catalogue requirement is probed.
area: scheduler, probe, catalogue, off-site copy
paid-for-by: 2026-10-19, founding session, track B 2a

The off-site copy and its rehearsal were merged with `requires` naming
`zstd`, `pg_restore` and `initdb`. All three are installed, but the probe
only asks `which` for its own fixed list, so the worker's profile held no
entry for them and `missing_programs` returned them every tick. The rows
sat queued for two hours with no log line, and tonight's 21:00 run would
have sat the same way. Found only because Arthur asked to run the copy by
day and the row did not move. The fix is three names in the list and a
test that reads the catalogue; the per-profile model servers are left to
their open card.
